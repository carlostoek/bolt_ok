import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot
from collections import defaultdict

from utils.message_safety import safe_send_message

logger = logging.getLogger(__name__)

class NotificationPriority:
    """Define prioridades para diferentes tipos de notificaciones."""
    CRITICAL = 0  # Errores, alertas importantes
    HIGH = 1      # Logros, niveles, misiones importantes
    MEDIUM = 2    # Puntos, misiones normales
    LOW = 3       # Reacciones, mensajes informativos

class NotificationData:
    """Representa una notificación pendiente de envío con prioridad."""
    
    def __init__(self, notification_type: str, data: Dict[str, Any], 
                 priority: int = NotificationPriority.MEDIUM, 
                 timestamp: datetime = None):
        self.type = notification_type
        self.data = data
        self.priority = priority
        self.timestamp = timestamp or datetime.now()
        self.hash = self._generate_hash()
    
    def _generate_hash(self) -> str:
        """Genera un hash único para evitar duplicados."""
        key_parts = [self.type]
        if self.type == "points":
            key_parts.append(str(self.data.get("points", 0)))
        elif self.type == "mission":
            key_parts.append(self.data.get("name", ""))
        elif self.type == "mission_completed":
            key_parts.append(self.data.get("mission_id", ""))
        elif self.type == "achievement":
            key_parts.append(self.data.get("name", ""))
        return "_".join(key_parts)

class NotificationService:
    """
    Servicio centralizado para manejo de notificaciones con agregación temporal inteligente.
    Consolida notificaciones relacionadas en un solo mensaje para mejorar la experiencia.
    """
    
    def __init__(self, session: AsyncSession, bot: Bot):
        self.session = session
        self.bot = bot
        self.pending_notifications: Dict[int, List[NotificationData]] = defaultdict(list)
        self.scheduled_tasks: Dict[int, asyncio.Task] = {}
        self.processed_hashes: Dict[int, Set[str]] = defaultdict(set)
        
        # Configuración de delays por prioridad
        self.aggregation_delays = {
            NotificationPriority.CRITICAL: 0.1,  # Casi inmediato
            NotificationPriority.HIGH: 0.5,      # Medio segundo
            NotificationPriority.MEDIUM: 1.0,    # Un segundo
            NotificationPriority.LOW: 1.5        # Segundo y medio
        }
        
        # Límite de notificaciones en cola antes de forzar envío
        self.max_queue_size = 10
        
    async def add_notification(self, user_id: int, notification_type: str, 
                              data: Dict[str, Any], 
                              priority: int = NotificationPriority.MEDIUM) -> None:
        """
        Añade una notificación a la cola con detección de duplicados.
        
        Args:
            user_id: ID del usuario de Telegram
            notification_type: Tipo de notificación
            data: Datos específicos de la notificación
            priority: Prioridad de la notificación
        """
        try:
            notification = NotificationData(notification_type, data, priority)
            
            # Verificar duplicados
            if notification.hash in self.processed_hashes[user_id]:
                logger.debug(f"Skipping duplicate notification {notification.hash} for user {user_id}")
                return
            
            # Añadir a procesados
            self.processed_hashes[user_id].add(notification.hash)
            
            # Añadir a la cola
            self.pending_notifications[user_id].append(notification)
            
            # Verificar si debemos enviar inmediatamente
            should_send_now = (
                len(self.pending_notifications[user_id]) >= self.max_queue_size or
                priority == NotificationPriority.CRITICAL
            )
            
            if should_send_now:
                # Enviar inmediatamente si es crítico o la cola está llena
                await self._send_notifications_now(user_id)
            else:
                # Programar envío con delay según prioridad
                await self._schedule_send_with_priority(user_id, priority)
            
            logger.debug(f"Added {notification_type} notification for user {user_id} with priority {priority}")
            
        except Exception as e:
            logger.exception(f"Error adding notification for user {user_id}: {e}")
    
    async def _schedule_send_with_priority(self, user_id: int, priority: int) -> None:
        """Programa el envío con delay basado en prioridad."""
        # Cancelar tarea anterior si existe
        if user_id in self.scheduled_tasks:
            self.scheduled_tasks[user_id].cancel()
        
        # Obtener delay según prioridad
        delay = self.aggregation_delays.get(priority, 1.0)
        
        # Programar nueva tarea
        self.scheduled_tasks[user_id] = asyncio.create_task(
            self._delayed_send(user_id, delay)
        )
    
    async def _delayed_send(self, user_id: int, delay: float) -> None:
        """Envía notificaciones después del delay especificado."""
        try:
            await asyncio.sleep(delay)
            await self._send_notifications_now(user_id)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.exception(f"Error in delayed send for user {user_id}: {e}")
    
    async def _send_notifications_now(self, user_id: int) -> None:
        """Envía todas las notificaciones pendientes inmediatamente."""
        try:
            if user_id not in self.pending_notifications:
                return
            
            notifications = self.pending_notifications.pop(user_id, [])
            
            if not notifications:
                return
            
            # Limpiar tarea programada
            if user_id in self.scheduled_tasks:
                del self.scheduled_tasks[user_id]
            
            # Ordenar por prioridad
            notifications.sort(key=lambda n: (n.priority, n.timestamp))
            
            # Agrupar por tipo
            grouped = self._group_notifications_by_type(notifications)
            
            # Construir mensaje unificado
            message = await self._build_enhanced_unified_message(grouped)
            
            if message:
                await safe_send_message(self.bot, user_id, message, parse_mode="Markdown")
                logger.info(f"Sent unified notification to user {user_id}: {len(notifications)} items")
            
            # Limpiar hashes procesados después de un tiempo
            asyncio.create_task(self._cleanup_processed_hashes(user_id))
            
        except Exception as e:
            logger.exception(f"Error sending notifications for user {user_id}: {e}")
    
    async def _cleanup_processed_hashes(self, user_id: int, delay: int = 60) -> None:
        """Limpia los hashes procesados después de un tiempo."""
        await asyncio.sleep(delay)
        if user_id in self.processed_hashes:
            self.processed_hashes[user_id].clear()
    
    def _group_notifications_by_type(self, notifications: List[NotificationData]) -> Dict[str, List[Dict[str, Any]]]:
        """Agrupa notificaciones por tipo para consolidación."""
        grouped = defaultdict(list)
        for notification in notifications:
            grouped[notification.type].append(notification.data)
        return dict(grouped)
    
    async def _build_enhanced_unified_message(self, grouped: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        Construye un mensaje unificado mejorado con formato atractivo.
        
        El mensaje sigue esta estructura:
        1. Saludo personalizado de Diana
        2. Resumen de recompensas principales
        3. Detalles de cada tipo de notificación
        4. Mensaje motivacional de cierre
        """
        try:
            sections = []
            total_points = 0
            has_achievement = False
            has_level_up = False
            
            # === SECCIÓN DE ENCABEZADO ===
            header = "💋 *Diana te observa con una sonrisa cálida...*\n"
            sections.append(header)
            
            # === SECCIÓN DE PUNTOS Y RECOMPENSAS ===
            rewards_section = []
            
            # Procesar puntos totales
            if "points" in grouped:
                points_data = grouped["points"]
                total_new_points = sum(p.get("points", 0) for p in points_data)
                latest_total = points_data[-1].get("total", 0)
                
                if total_new_points > 0:
                    total_points = total_new_points
                    rewards_section.append(f"✨ *+{total_new_points} besitos* ganados")
                    rewards_section.append(f"💰 *Tesoro actual:* {latest_total} besitos")
            
            # Procesar misiones (sistema antiguo)
            if "mission" in grouped:
                missions = grouped["mission"]
                mission_points = sum(m.get("points", 0) for m in missions)
                
                if len(missions) == 1:
                    mission = missions[0]
                    rewards_section.append(f"🎯 *Misión completada:* _{mission.get('name', 'Misión Secreta')}_")
                    if mission_points > 0:
                        rewards_section.append(f"   → Recompensa: +{mission_points} besitos")
                else:
                    rewards_section.append(f"🎯 *{len(missions)} misiones completadas*")
                    for mission in missions[:3]:  # Mostrar máximo 3
                        rewards_section.append(f"   • {mission.get('name', 'Misión')}")
                    if len(missions) > 3:
                        rewards_section.append(f"   • _...y {len(missions)-3} más_")
                        
            # Procesar misiones unificadas
            if "mission_completed" in grouped:
                missions = grouped["mission_completed"]
                
                if len(missions) == 1:
                    mission = missions[0]
                    rewards_section.append(f"✨ *Misión Unificada Completada:* _{mission.get('title', 'Misión Especial')}_")
                    
                    # Mostrar recompensas detalladas
                    rewards_data = mission.get('rewards', {})
                    if rewards_data:
                        reward_items = []
                        
                        if 'points' in rewards_data and rewards_data['points'] > 0:
                            reward_items.append(f"+{rewards_data['points']} besitos")
                            
                        if 'lore_pieces' in rewards_data and rewards_data['lore_pieces']:
                            count = len(rewards_data['lore_pieces'])
                            reward_items.append(f"{count} pista{'s' if count > 1 else ''}")
                            
                        if 'badges' in rewards_data and rewards_data['badges']:
                            count = len(rewards_data['badges'])
                            reward_items.append(f"{count} insignia{'s' if count > 1 else ''}")
                            
                        if reward_items:
                            rewards_section.append(f"   → Recompensas: {', '.join(reward_items)}")
                else:
                    rewards_section.append(f"✨ *{len(missions)} Misiones Unificadas Completadas*")
                    for mission in missions[:3]:  # Mostrar máximo 3
                        rewards_section.append(f"   • {mission.get('title', 'Misión')}")
                    if len(missions) > 3:
                        rewards_section.append(f"   • _...y {len(missions)-3} más_")
            
            # === SECCIÓN DE LOGROS Y PROGRESO ===
            progress_section = []
            
            # Procesar logros
            if "achievement" in grouped:
                has_achievement = True
                achievements = grouped["achievement"]
                
                if len(achievements) == 1:
                    ach = achievements[0]
                    progress_section.append(f"🏆 *¡LOGRO DESBLOQUEADO!*")
                    progress_section.append(f"_{ach.get('name', 'Logro Misterioso')}_")
                    if ach.get('description'):
                        progress_section.append(f"_{ach['description']}_")
                else:
                    progress_section.append(f"🏆 *¡{len(achievements)} LOGROS DESBLOQUEADOS!*")
                    for ach in achievements[:2]:
                        progress_section.append(f"   • {ach.get('name', 'Logro')}")
            
            # Procesar subidas de nivel
            if "level" in grouped:
                has_level_up = True
                levels = grouped["level"]
                latest = levels[-1]
                progress_section.append(f"⭐ *¡NUEVO NIVEL ALCANZADO!*")
                progress_section.append(f"Ahora eres nivel *{latest.get('level', 'N/A')}*")
                if latest.get('title'):
                    progress_section.append(f"_Título: {latest['title']}_")
            
            # Procesar insignias
            if "badge" in grouped:
                badges = grouped["badge"]
                if len(badges) == 1:
                    badge = badges[0]
                    icon = badge.get('icon', '🎖')
                    progress_section.append(f"{icon} *Nueva insignia:* {badge.get('name', 'Insignia Secreta')}")
                else:
                    progress_section.append(f"🎖 *{len(badges)} nuevas insignias obtenidas*")
            
            # === SECCIÓN DE NARRATIVA ===
            narrative_section = []
            
            # Procesar pistas narrativas
            if "hint" in grouped:
                hints = grouped["hint"]
                latest_hint = hints[-1]
                narrative_section.append("📜 *Una nueva pista se revela...*")
                narrative_section.append(f"_\"{latest_hint.get('text', 'Los secretos se revelan a quienes perseveran...')}\"_")
            
            # Procesar acceso VIP
            if "vip_access" in grouped:
                narrative_section.append("🔓 *Acceso VIP desbloqueado*")
                narrative_section.append("_Nuevos secretos te esperan en el reino privado..._")
            
            # === CONSTRUIR MENSAJE FINAL ===
            
            # Añadir sección de recompensas
            if rewards_section:
                sections.append("━━━━━━━━━━━━━━━")
                sections.extend(rewards_section)
            
            # Añadir sección de progreso (con énfasis especial)
            if progress_section:
                sections.append("━━━━━━━━━━━━━━━")
                sections.extend(progress_section)
            
            # Añadir sección narrativa
            if narrative_section:
                sections.append("━━━━━━━━━━━━━━━")
                sections.extend(narrative_section)
            
            # === MENSAJE DE CIERRE CONTEXTUAL ===
            sections.append("━━━━━━━━━━━━━━━")
            
            if has_achievement or has_level_up:
                closing = "*\"Has superado mis expectativas, mi amor... Continúa así y pronto todos mis secretos serán tuyos.\"* 💋"
            elif total_points > 50:
                closing = "*\"Impresionante progreso... Me gusta ver tu dedicación.\"* 💋"
            elif "hint" in grouped:
                closing = "*\"Cada pista te acerca más a la verdad... y a mí.\"* 💋"
            else:
                closing = "*\"Cada interacción nos acerca más... No te detengas ahora.\"* 💋"
            
            sections.append(closing)
            
            return "\n".join(sections)
            
        except Exception as e:
            logger.exception(f"Error building enhanced message: {e}")
            # Mensaje de fallback
            return "💋 *Diana te envía una sonrisa misteriosa...*\n\nHas progresado en tu viaje. ¡Continúa explorando!"
    
    async def send_immediate_notification(self, user_id: int, message: str, 
                                         priority: int = NotificationPriority.HIGH) -> None:
        """
        Envía una notificación inmediata sin agregación.
        Útil para notificaciones críticas o de error.
        """
        try:
            # Cancelar cualquier envío programado
            if user_id in self.scheduled_tasks:
                self.scheduled_tasks[user_id].cancel()
            
            # Enviar notificaciones pendientes primero si existen
            if user_id in self.pending_notifications and self.pending_notifications[user_id]:
                await self._send_notifications_now(user_id)
            
            # Enviar la notificación inmediata
            await safe_send_message(self.bot, user_id, message, parse_mode="Markdown")
            logger.info(f"Sent immediate notification to user {user_id}")
            
        except Exception as e:
            logger.exception(f"Error sending immediate notification to user {user_id}: {e}")
    
    async def flush_pending_notifications(self, user_id: int) -> None:
        """
        Fuerza el envío inmediato de todas las notificaciones pendientes.
        Útil para asegurar que el usuario reciba todo antes de una desconexión.
        """
        try:
            if user_id in self.scheduled_tasks:
                self.scheduled_tasks[user_id].cancel()
            
            await self._send_notifications_now(user_id)
            logger.info(f"Flushed all pending notifications for user {user_id}")
            
        except Exception as e:
            logger.exception(f"Error flushing notifications for user {user_id}: {e}")
    
    def get_pending_count(self, user_id: int) -> int:
        """Obtiene el número de notificaciones pendientes para un usuario."""
        return len(self.pending_notifications.get(user_id, []))
    
    async def cleanup_user(self, user_id: int) -> None:
        """Limpia todos los datos relacionados con un usuario."""
        try:
            # Cancelar tareas
            if user_id in self.scheduled_tasks:
                self.scheduled_tasks[user_id].cancel()
                del self.scheduled_tasks[user_id]
            
            # Limpiar notificaciones pendientes
            if user_id in self.pending_notifications:
                del self.pending_notifications[user_id]
            
            # Limpiar hashes procesados
            if user_id in self.processed_hashes:
                del self.processed_hashes[user_id]
            
            logger.info(f"Cleaned up notification data for user {user_id}")
            
        except Exception as e:
            logger.exception(f"Error cleaning up user {user_id}: {e}")