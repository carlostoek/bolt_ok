"""
Coordinador Central para orquestar la integración entre todos los módulos del sistema.
"""
import logging
import enum
import asyncio
from typing import Dict, Any, Optional, Callable, Union, List
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession

from .integration.channel_engagement_service import ChannelEngagementService
from .integration.narrative_point_service import NarrativePointService
from .integration.narrative_access_service import NarrativeAccessService
from .integration.event_coordinator import EventCoordinator
from .narrative_service import NarrativeService
from .point_service import PointService
from .mission_service import MissionService
from .reconciliation_service import ReconciliationService
from .event_bus import get_event_bus, EventType, Event
from .notification_service import NotificationService
from .user_service import UserService

logger = logging.getLogger(__name__)

class AccionUsuario(enum.Enum):
    """Enumeración de acciones de usuario que pueden desencadenar flujos integrados."""
    REACCIONAR_PUBLICACION = "reaccionar_publicacion"
    ACCEDER_NARRATIVA_VIP = "acceder_narrativa_vip"
    TOMAR_DECISION = "tomar_decision"
    PARTICIPAR_CANAL = "participar_canal"
    VERIFICAR_ENGAGEMENT = "verificar_engagement"

class CoordinadorCentral:
    """
    Coordinador central que orquesta la interacción entre los diferentes módulos del sistema.
    Implementa el patrón Facade para simplificar la interacción con los subsistemas.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Inicializa el coordinador con los servicios de integración necesarios.
        
        Args:
            session: Sesión de base de datos para los servicios
        """
        self.session = session
        # Servicios de integración
        self.channel_engagement = ChannelEngagementService(session)
        self.narrative_point = NarrativePointService(session)
        self.narrative_access = NarrativeAccessService(session)
        self.event_coordinator = EventCoordinator(session)
        # Servicios base
        self.narrative_service = NarrativeService(session)
        self.point_service = PointService(session)
        self.mission_service = MissionService(session)
        self.reconciliation_service = ReconciliationService(session)
        self.user_service = UserService(session)
        # Event bus for inter-module communication
        self.event_bus = get_event_bus()
    
    async def ejecutar_flujo(self, user_id: int, accion: AccionUsuario, **kwargs) -> Dict[str, Any]:
        """
        Ejecuta un flujo completo basado en la acción del usuario.
        
        Args:
            user_id: ID del usuario de Telegram
            accion: Tipo de acción realizada por el usuario
            **kwargs: Parámetros adicionales específicos de la acción
            
        Returns:
            Dict con los resultados del flujo y mensajes para el usuario
        """
        try:
            # Obtener bot si está disponible para crear servicio de notificaciones
            bot = kwargs.get('bot')
            notification_service = None
            if bot:
                notification_service = NotificationService(self.session, bot)
            
            # Seleccionar el flujo adecuado según la acción
            if accion == AccionUsuario.REACCIONAR_PUBLICACION:
                result = await self._flujo_reaccion_publicacion(user_id, **kwargs)
                # Enviar notificaciones unificadas si está habilitado
                if notification_service and result.get("success") and not kwargs.get("skip_unified_notifications"):
                    await self._send_unified_notifications(notification_service, user_id, result, accion)
                return result
            elif accion == AccionUsuario.ACCEDER_NARRATIVA_VIP:
                return await self._flujo_acceso_narrativa_vip(user_id, **kwargs)
            elif accion == AccionUsuario.TOMAR_DECISION:
                return await self._flujo_tomar_decision(user_id, **kwargs)
            elif accion == AccionUsuario.PARTICIPAR_CANAL:
                result = await self._flujo_participacion_canal(user_id, **kwargs)
                # Enviar notificaciones unificadas si está habilitado
                if notification_service and result.get("success") and not kwargs.get("skip_unified_notifications"):
                    await self._send_unified_notifications(notification_service, user_id, result, accion)
                return result
            elif accion == AccionUsuario.VERIFICAR_ENGAGEMENT:
                result = await self._flujo_verificar_engagement(user_id, **kwargs)
                # Enviar notificaciones unificadas si está habilitado
                if notification_service and result.get("success") and not kwargs.get("skip_unified_notifications"):
                    await self._send_unified_notifications(notification_service, user_id, result, accion)
                return result
            else:
                logger.warning(f"Acción no implementada: {accion}")
                return {
                    "success": False,
                    "message": "Acción no reconocida por el sistema."
                }
        except Exception as e:
            logger.exception(f"Error en flujo {accion}: {str(e)}")
            return {
                "success": False,
                "message": "Un error inesperado ha ocurrido. Inténtalo de nuevo más tarde.",
                "error": str(e)
            }
    
    async def _flujo_reaccion_publicacion(self, user_id: int, message_id: int, channel_id: int, reaction_type: str, bot=None) -> Dict[str, Any]:
        """
        Flujo para manejar reacciones a publicaciones en canales.
        
        Args:
            user_id: ID del usuario
            message_id: ID del mensaje al que se reaccionó
            channel_id: ID del canal donde está el mensaje
            reaction_type: Tipo de reacción (emoji)
            bot: Instancia del bot para enviar mensajes
            
        Returns:
            Dict con resultados y mensajes
        """
        # 1. Otorgar puntos por la reacción
        puntos_otorgados = await self.channel_engagement.award_channel_reaction(
            user_id, message_id, channel_id, bot=bot, skip_direct_notifications=True
        )
        
        if not puntos_otorgados:
            return {
                "success": False,
                "message": "Diana observa tu gesto desde lejos, pero no parece haberlo notado... Intenta de nuevo más tarde.",
                "action": "reaction_failed"
            }
        
        # 2. Verificar y completar misiones de reacción
        misiones_completadas = []
        try:
            # Buscar misiones de reacción activas
            misiones_reaccion = await self.mission_service.get_active_missions(user_id=user_id, mission_type="reaction")
            for mision in misiones_reaccion:
                # Intentar completar la misión
                completada, mision_obj = await self.mission_service.complete_mission(
                    user_id, mision.id, reaction_type=reaction_type, 
                    target_message_id=message_id, bot=bot, _skip_notification=True
                )
                if completada:
                    misiones_completadas.append({
                        "name": mision_obj.name,
                        "points": mision_obj.reward_points
                    })
                    logger.info(f"Mission {mision.id} completed for user {user_id} via reaction")
        except Exception as e:
            logger.exception(f"Error checking reaction missions for user {user_id}: {e}")

        # 3. Obtener puntos actuales del usuario (después de misiones)
        puntos_actuales = await self.point_service.get_user_points(user_id)
        
        # 4. Verificar si se desbloquea una pista narrativa
        pista_desbloqueada = None
        if puntos_actuales % 50 <= 15 and puntos_actuales > 15:  # Desbloquear pista cada ~50 puntos
            # Obtener fragmento actual del usuario
            fragmento_actual = await self.narrative_service.get_user_current_fragment(user_id)
            if fragmento_actual:
                # Simular desbloqueo de pista basada en el fragmento actual
                pistas = {
                    "level1_": "El jardín de los secretos esconde más de lo que revela a simple vista...",
                    "level2_": "Las sombras del pasillo susurran verdades que nadie se atreve a pronunciar...",
                    "level3_": "Bajo la luz de la luna, los amantes intercambian más que simples caricias...",
                    "level4_": "El sabor prohibido de sus labios esconde un secreto ancestral...",
                    "level5_": "En la habitación del placer, las reglas convencionales se desvanecen...",
                    "level6_": "El último velo cae, revelando la verdad que siempre estuvo ante tus ojos..."
                }
                
                for prefix, pista in pistas.items():
                    if fragmento_actual.key.startswith(prefix):
                        pista_desbloqueada = pista
                        break
        
        # 5. Generar mensaje de respuesta
        mensaje_base = "Diana sonríe al notar tu reacción... *+10 besitos* 💋 han sido añadidos a tu cuenta."
        if pista_desbloqueada:
            mensaje = f"{mensaje_base}\n\n*Nueva pista desbloqueada:* _{pista_desbloqueada}_"
        else:
            mensaje = mensaje_base
        
        return {
            "success": True,
            "message": mensaje,
            "points_awarded": 10,
            "total_points": puntos_actuales,
            "hint_unlocked": pista_desbloqueada,
            "missions_completed": misiones_completadas,
            "action": "reaction_success"
        }
    
    async def _flujo_acceso_narrativa_vip(self, user_id: int, fragment_key: str, bot=None) -> Dict[str, Any]:
        """
        Flujo para manejar intentos de acceso a contenido narrativo VIP.
        
        Args:
            user_id: ID del usuario
            fragment_key: Clave del fragmento solicitado
            bot: Instancia del bot para enviar mensajes
            
        Returns:
            Dict con resultados y mensajes
        """
        # 1. Verificar acceso al fragmento
        fragment_result = await self.narrative_access.get_accessible_fragment(user_id, fragment_key)
        
        # 2. Procesar resultado
        if isinstance(fragment_result, dict) and fragment_result.get("type") == "subscription_required":
            return {
                "success": False,
                "message": "Diana te mira con deseo, pero niega suavemente con la cabeza...\n\n*\"Este contenido requiere una suscripción VIP, mi amor. Algunas fantasías son solo para mis amantes más dedicados...\"*\n\nUsa /vip para acceder a contenido exclusivo.",
                "action": "vip_required",
                "fragment_key": fragment_key
            }
        
        # 3. Acceso permitido, devolver fragmento
        return {
            "success": True,
            "message": "Diana te toma de la mano y te guía hacia un nuevo capítulo de vuestra historia...",
            "fragment": fragment_result,
            "action": "fragment_accessed"
        }
    
    async def _flujo_tomar_decision(self, user_id: int, decision_id: int, bot=None) -> Dict[str, Any]:
        """
        Flujo para manejar decisiones narrativas del usuario.
        
        Args:
            user_id: ID del usuario
            decision_id: ID de la decisión tomada
            bot: Instancia del bot para enviar mensajes
            
        Returns:
            Dict con resultados y mensajes
        """
        # 1. Procesar la decisión con verificación de puntos
        decision_result = await self.narrative_point.process_decision_with_points(user_id, decision_id, bot)
        
        # 2. Verificar resultado
        if decision_result["type"] == "points_required":
            return {
                "success": False,
                "message": "Diana suspira con anhelo...\n\n*\"Esta decisión requiere más besitos de los que tienes ahora, mi amor. Algunas fantasías necesitan más... intensidad.\"*\n\nNecesitas más besitos para esta elección. Participa en los canales para conseguir más.",
                "action": "points_required",
                "decision_id": decision_id
            }
        elif decision_result["type"] == "error":
            return {
                "success": False,
                "message": "Diana parece confundida por tu elección...\n\n*\"No logro entender lo que deseas, mi amor. ¿Podrías intentarlo de nuevo?\"*",
                "action": "decision_error",
                "error": decision_result["message"]
            }
        
        # 3. Decisión exitosa
        return {
            "success": True,
            "message": "Diana asiente con una sonrisa seductora mientras la historia toma un nuevo rumbo...",
            "fragment": decision_result["fragment"],
            "action": "decision_success"
        }
    
    async def _flujo_participacion_canal(self, user_id: int, channel_id: int, action_type: str, bot=None) -> Dict[str, Any]:
        """
        Flujo para manejar participación en canales (mensajes, comentarios, etc).
        
        Args:
            user_id: ID del usuario
            channel_id: ID del canal
            action_type: Tipo de acción (post, comment, etc)
            bot: Instancia del bot para enviar mensajes
            
        Returns:
            Dict con resultados y mensajes
        """
        # 1. Otorgar puntos por participación
        participacion_exitosa = await self.channel_engagement.award_channel_participation(
            user_id, channel_id, action_type, bot
        )
        
        if not participacion_exitosa:
            return {
                "success": False,
                "message": "Diana nota tu participación, pero parece que algo no ha funcionado correctamente...",
                "action": "participation_failed"
            }
        
        # 2. Determinar puntos otorgados según el tipo de acción
        puntos = 5 if action_type == "post" else 2 if action_type == "comment" else 1
        
        # 3. Generar mensaje según tipo de acción
        mensajes = {
            "post": "Diana lee con interés tu publicación, sus ojos brillan de emoción...\n\n*+5 besitos* 💋 por compartir tus pensamientos.",
            "comment": "Diana sonríe al leer tu comentario, mordiendo suavemente su labio inferior...\n\n*+2 besitos* 💋 por tu participación.",
            "poll_vote": "Diana asiente al ver tu voto, apreciando tu opinión...\n\n*+1 besito* 💋 por participar.",
            "message": "Diana nota tu mensaje, un suave rubor colorea sus mejillas...\n\n*+1 besito* 💋 por tu actividad."
        }
        
        mensaje = mensajes.get(action_type, "Diana aprecia tu participación...\n\n*+1 besito* 💋 añadido.")
        
        return {
            "success": True,
            "message": mensaje,
            "points_awarded": puntos,
            "action": "participation_success",
            "action_type": action_type
        }
    
    async def _flujo_verificar_engagement(self, user_id: int, bot=None) -> Dict[str, Any]:
        """
        Flujo para verificar engagement diario y otorgar bonificaciones.
        
        Args:
            user_id: ID del usuario
            bot: Instancia del bot para enviar mensajes
            
        Returns:
            Dict con resultados y mensajes
        """
        # 1. Verificar engagement diario
        engagement_result = await self.channel_engagement.check_daily_engagement(user_id, bot)
        
        if not engagement_result:
            return {
                "success": False,
                "message": "Diana te observa con una sonrisa paciente...\n\n*\"Ya nos hemos visto hoy, mi amor. Regresa mañana para más recompensas...\"*",
                "action": "daily_check_already_done"
            }
        
        # 2. Obtener información de progreso
        user_data = await self.user_service.get_user(user_id)
        # Note: streak information would need to be tracked elsewhere or in a separate service
        streak = 1  # Default value since streak is not directly in User model
        
        # 3. Generar mensaje según racha
        if streak % 7 == 0:  # Racha semanal
            mensaje = f"Diana te recibe con un abrazo apasionado...\n\n*\"¡Has vuelto por {streak} días consecutivos, mi amor! Tu dedicación merece una recompensa especial...\"*\n\n*+25 besitos* 💋 por tu constancia semanal."
        else:
            mensaje = f"Diana te recibe con una sonrisa cálida...\n\n*\"Me alegra verte de nuevo, mi amor. Este es tu día {streak} consecutivo visitándome...\"*\n\n*+10 besitos* 💋 por tu visita diaria."
        
        return {
            "success": True,
            "message": mensaje,
            "streak": streak,
            "points_awarded": 25 if streak % 7 == 0 else 10,
            "action": "daily_check_success"
        }
    
    # ==================== ENHANCED ASYNC WORKFLOW CAPABILITIES ====================
    
    async def ejecutar_flujo_async(self, user_id: int, accion: AccionUsuario, **kwargs) -> Dict[str, Any]:
        """
        Enhanced asynchronous workflow execution with event integration.
        Maintains backward compatibility while adding event-driven capabilities.
        
        Args:
            user_id: ID del usuario de Telegram
            accion: Tipo de acción realizada por el usuario
            **kwargs: Parámetros adicionales específicos de la acción
            
        Returns:
            Dict con los resultados del flujo y mensajes para el usuario
        """
        correlation_id = kwargs.get('correlation_id', f"{accion.value}_{user_id}_{asyncio.current_task().get_name() if asyncio.current_task() else 'unknown'}")
        
        try:
            # Execute the regular workflow
            result = await self.ejecutar_flujo(user_id, accion, **kwargs)
            
            # Emit workflow completion event
            await self._emit_workflow_events(user_id, accion, result, correlation_id)
            
            return result
            
        except Exception as e:
            logger.exception(f"Error in async workflow {accion}: {str(e)}")
            
            # Emit error event
            await self.event_bus.publish(
                EventType.ERROR_OCCURRED,
                user_id,
                {
                    "workflow": accion.value,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "source": "coordinador_central"
                },
                source="coordinador_central",
                correlation_id=correlation_id
            )
            
            return {
                "success": False,
                "message": "Un error inesperado ha ocurrido. Inténtalo de nuevo más tarde.",
                "error": str(e),
                "correlation_id": correlation_id
            }
    
    @asynccontextmanager
    async def with_transaction(self, workflow_func: Callable, *args, **kwargs):
        """
        Context manager for executing workflows within database transactions.
        Provides atomic operation capabilities for complex multi-service workflows.
        
        Args:
            workflow_func: Async function to execute within transaction
            *args, **kwargs: Arguments to pass to workflow_func
            
        Yields:
            Transaction context where workflow_func will be executed
            
        Example:
            async with coordinador.with_transaction(self._complex_workflow, user_id, data) as result:
                # Additional post-transaction logic here
                pass
        """
        async with self.session.begin() as transaction:
            try:
                result = await workflow_func(*args, **kwargs)
                # Transaction will be committed automatically if no exception
                yield result
            except Exception as e:
                # Transaction will be rolled back automatically
                logger.exception(f"Transaction failed in workflow: {e}")
                raise
    
    async def execute_parallel_workflows(self, workflows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute multiple workflows in parallel for improved performance.
        Maintains data consistency by ensuring workflows don't interfere with each other.
        
        Args:
            workflows: List of workflow specifications, each containing:
                - user_id: int
                - accion: AccionUsuario
                - kwargs: dict of additional parameters
                
        Returns:
            List[Dict]: Results from each workflow in the same order
        """
        correlation_id = f"parallel_{asyncio.current_task().get_name() if asyncio.current_task() else 'unknown'}"
        
        async def execute_single_workflow(workflow_spec: Dict[str, Any]) -> Dict[str, Any]:
            """Execute a single workflow with error isolation."""
            try:
                workflow_spec.setdefault('kwargs', {})['correlation_id'] = correlation_id
                return await self.ejecutar_flujo_async(
                    workflow_spec['user_id'],
                    workflow_spec['accion'],
                    **workflow_spec.get('kwargs', {})
                )
            except Exception as e:
                logger.exception(f"Error in parallel workflow execution: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "user_id": workflow_spec.get('user_id'),
                    "accion": workflow_spec.get('accion', {}).value if workflow_spec.get('accion') else 'unknown'
                }
        
        # Execute all workflows concurrently
        tasks = [execute_single_workflow(workflow) for workflow in workflows]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error dictionaries
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "workflow_index": i,
                    "correlation_id": correlation_id
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _emit_workflow_events(self, user_id: int, accion: AccionUsuario, 
                                   result: Dict[str, Any], correlation_id: str) -> None:
        """
        Emit appropriate events based on workflow execution results.
        Provides event-driven integration between modules.
        
        Args:
            user_id: User ID
            accion: Action that was executed
            result: Workflow execution result
            correlation_id: Correlation ID for event tracking
        """
        try:
            # Base workflow completion event
            await self.event_bus.publish(
                EventType.WORKFLOW_COMPLETED,
                user_id,
                {
                    "workflow": accion.value,
                    "success": result.get("success", False),
                    "action": result.get("action", "unknown"),
                    "result_summary": {
                        "points_awarded": result.get("points_awarded"),
                        "message_sent": bool(result.get("message")),
                        "additional_data": {k: v for k, v in result.items() 
                                         if k not in ['success', 'message', 'error']}
                    }
                },
                source="coordinador_central",
                correlation_id=correlation_id
            )
            
            # Specific events based on action type and results
            if result.get("success"):
                if accion == AccionUsuario.REACCIONAR_PUBLICACION:
                    await self.event_bus.publish(
                        EventType.USER_REACTION,
                        user_id,
                        {
                            "points_awarded": result.get("points_awarded", 0),
                            "hint_unlocked": result.get("hint_unlocked"),
                            "total_points": result.get("total_points", 0)
                        },
                        source="coordinador_central",
                        correlation_id=correlation_id
                    )
                    
                    if result.get("points_awarded", 0) > 0:
                        await self.event_bus.publish(
                            EventType.POINTS_AWARDED,
                            user_id,
                            {
                                "points": result.get("points_awarded"),
                                "source": "channel_reaction",
                                "total_points": result.get("total_points", 0)
                            },
                            source="coordinador_central",
                            correlation_id=correlation_id
                        )
                
                elif accion == AccionUsuario.TOMAR_DECISION:
                    await self.event_bus.publish(
                        EventType.NARRATIVE_DECISION,
                        user_id,
                        {
                            "decision_id": result.get("decision_id"),
                            "fragment": result.get("fragment", {}).get("key") if result.get("fragment") else None
                        },
                        source="coordinador_central",
                        correlation_id=correlation_id
                    )
                
                elif accion == AccionUsuario.PARTICIPAR_CANAL:
                    await self.event_bus.publish(
                        EventType.CHANNEL_ENGAGEMENT,
                        user_id,
                        {
                            "action_type": result.get("action_type"),
                            "points_awarded": result.get("points_awarded", 0)
                        },
                        source="coordinador_central",
                        correlation_id=correlation_id
                    )
                
                elif accion == AccionUsuario.VERIFICAR_ENGAGEMENT:
                    await self.event_bus.publish(
                        EventType.USER_DAILY_CHECKIN,
                        user_id,
                        {
                            "streak": result.get("streak", 1),
                            "points_awarded": result.get("points_awarded", 0)
                        },
                        source="coordinador_central",
                        correlation_id=correlation_id
                    )
            
            else:
                # Handle failure cases
                if accion == AccionUsuario.ACCEDER_NARRATIVA_VIP and result.get("action") == "vip_required":
                    await self.event_bus.publish(
                        EventType.VIP_ACCESS_REQUIRED,
                        user_id,
                        {
                            "fragment_key": result.get("fragment_key"),
                            "workflow": accion.value
                        },
                        source="coordinador_central",
                        correlation_id=correlation_id
                    )
                
        except Exception as e:
            # Don't let event emission failures break the main workflow
            logger.exception(f"Error emitting workflow events: {e}")
    
    # ==================== CONSISTENCY AND MONITORING ====================
    
    async def check_system_consistency(self, user_id: int) -> Dict[str, Any]:
        """
        Perform consistency checks across all user-related data.
        Helps identify and report data inconsistencies between modules.
        
        Args:
            user_id: User ID to check consistency for
            
        Returns:
            Dict containing consistency check results
        """
        try:
            # Use the comprehensive reconciliation service
            reconciliation_result = await self.reconciliation_service.perform_full_reconciliation([user_id])
            
            # Convert reconciliation result to legacy format for backward compatibility
            consistency_report = {
                "user_id": user_id,
                "timestamp": asyncio.get_event_loop().time(),
                "checks": {
                    "user_exists": reconciliation_result.total_users_checked > 0,
                    "issues_found": reconciliation_result.inconsistencies_found,
                    "issues_corrected": reconciliation_result.inconsistencies_corrected
                },
                "warnings": [],
                "errors": [],
                "detailed_reports": reconciliation_result.reports
            }
            
            # Extract user data for compatibility
            user_data = await self.user_service.get_user(user_id)
            if user_data:
                current_points = await self.point_service.get_user_points(user_id)
                consistency_report["checks"]["points_consistent"] = current_points >= 0
                consistency_report["data"] = {
                    "current_points": current_points,
                    "level": getattr(user_data, 'level', 0),
                    "achievements": getattr(user_data, 'achievements', {})
                }
                
                # Check narrative consistency if user has narrative progress
                try:
                    current_fragment = await self.narrative_service.get_user_current_fragment(user_id)
                    consistency_report["checks"]["narrative_consistent"] = True
                    consistency_report["data"]["current_fragment"] = current_fragment.key if current_fragment else None
                except Exception as e:
                    consistency_report["checks"]["narrative_consistent"] = False
                    consistency_report["warnings"].append(f"Narrative check failed: {str(e)}")
            
            # Add detailed issue summaries
            for report in reconciliation_result.reports:
                if report.severity in ['high', 'critical']:
                    consistency_report["errors"].append(f"{report.issue_type}: {report.description}")
                else:
                    consistency_report["warnings"].append(f"{report.issue_type}: {report.description}")
            
            # Emit consistency check event
            await self.event_bus.publish(
                EventType.CONSISTENCY_CHECK,
                user_id,
                consistency_report,
                source="coordinador_central"
            )
            
            return consistency_report
            
        except Exception as e:
            logger.exception(f"Error in consistency check for user {user_id}: {e}")
            return {
                "user_id": user_id,
                "success": False,
                "error": str(e)
            }
    
    # ==================== ENHANCED COORDINATION CAPABILITIES ====================
    
    async def initialize_coordination_systems(self) -> Dict[str, Any]:
        """
        Initialize all coordination systems including event subscriptions.
        This should be called once during system startup.
        
        Returns:
            Dict containing initialization results
        """
        try:
            logger.info("Initializing coordination systems...")
            
            # Set up cross-module event subscriptions
            subscriptions = await self.event_coordinator.setup_cross_module_subscriptions()
            
            # Emit system initialization event
            await self.event_bus.publish(
                EventType.CONSISTENCY_CHECK,
                0,  # System-level event
                {
                    "type": "system_initialization",
                    "subscriptions_setup": subscriptions,
                    "coordination_active": True
                },
                source="coordinador_central"
            )
            
            logger.info(f"Coordination systems initialized: {sum(subscriptions.values())} event subscriptions active")
            
            return {
                "success": True,
                "subscriptions_setup": subscriptions,
                "total_subscriptions": sum(subscriptions.values()),
                "coordination_active": True
            }
            
        except Exception as e:
            logger.exception(f"Error initializing coordination systems: {e}")
            return {
                "success": False,
                "error": str(e),
                "coordination_active": False
            }
    
    async def perform_system_health_check(self) -> Dict[str, Any]:
        """
        Perform a comprehensive system health check across all modules.
        
        Returns:
            Dict containing health check results
        """
        try:
            logger.info("Starting comprehensive system health check...")
            
            health_report = {
                "timestamp": asyncio.get_event_loop().time(),
                "overall_status": "healthy",
                "modules": {},
                "event_system": {},
                "recommendations": []
            }
            
            # Check event system health
            event_status = self.event_coordinator.get_subscription_status()
            health_report["event_system"] = event_status
            
            if not event_status.get("subscriptions_active", False):
                health_report["overall_status"] = "degraded"
                health_report["recommendations"].append("Event subscriptions are not active - run initialize_coordination_systems()")
            
            # Perform reconciliation on a sample of users to check data integrity
            try:
                reconciliation_result = await self.reconciliation_service.perform_full_reconciliation()
                health_report["modules"]["reconciliation"] = {
                    "status": "healthy",
                    "users_checked": reconciliation_result.total_users_checked,
                    "issues_found": reconciliation_result.inconsistencies_found,
                    "issues_corrected": reconciliation_result.inconsistencies_corrected,
                    "execution_time_ms": reconciliation_result.execution_time_ms
                }
                
                # Assess data integrity
                if reconciliation_result.inconsistencies_found > reconciliation_result.total_users_checked * 0.1:  # More than 10% of users have issues
                    health_report["overall_status"] = "degraded"
                    health_report["recommendations"].append("High number of data inconsistencies detected - consider system maintenance")
                
            except Exception as e:
                health_report["modules"]["reconciliation"] = {
                    "status": "error",
                    "error": str(e)
                }
                health_report["overall_status"] = "unhealthy"
                health_report["recommendations"].append("Reconciliation service failed - check database connectivity")
            
            # Test basic service functionality
            try:
                # Test point service
                test_points = await self.point_service.get_user_points(999999999)  # Non-existent user should return 0
                health_report["modules"]["point_service"] = {
                    "status": "healthy",
                    "test_result": f"Non-existent user points: {test_points}"
                }
            except Exception as e:
                health_report["modules"]["point_service"] = {
                    "status": "error",
                    "error": str(e)
                }
                health_report["overall_status"] = "unhealthy"
            
            # Test narrative service
            try:
                test_fragment = await self.narrative_service.get_user_current_fragment(999999999)
                health_report["modules"]["narrative_service"] = {
                    "status": "healthy",
                    "test_result": f"Non-existent user fragment: {test_fragment}"
                }
            except Exception as e:
                health_report["modules"]["narrative_service"] = {
                    "status": "error",
                    "error": str(e)
                }
                health_report["overall_status"] = "unhealthy"
            
            # Emit health check event
            await self.event_bus.publish(
                EventType.CONSISTENCY_CHECK,
                0,  # System-level event
                {
                    "type": "system_health_check",
                    "result": health_report
                },
                source="coordinador_central"
            )
            
            logger.info(f"System health check completed: status = {health_report['overall_status']}")
            return health_report
            
        except Exception as e:
            logger.exception(f"Error during system health check: {e}")
            return {
                "timestamp": asyncio.get_event_loop().time(),
                "overall_status": "error",
                "error": str(e),
                "recommendations": ["System health check failed - investigate coordinator_central errors"]
            }
    
    async def get_coordination_status(self) -> Dict[str, Any]:
        """
        Get current status of all coordination systems.
        
        Returns:
            Dict containing status information for all coordination components
        """
        try:
            status = {
                "coordinador_central": {
                    "active": True,
                    "session_active": self.session is not None,
                    "services_loaded": {
                        "channel_engagement": self.channel_engagement is not None,
                        "narrative_point": self.narrative_point is not None,
                        "narrative_access": self.narrative_access is not None,
                        "event_coordinator": self.event_coordinator is not None,
                        "reconciliation_service": self.reconciliation_service is not None
                    }
                },
                "event_system": self.event_coordinator.get_subscription_status(),
                "event_history": len(self.event_bus.get_event_history(10))
            }
            
            return status
            
        except Exception as e:
            logger.exception(f"Error getting coordination status: {e}")
            return {
                "error": str(e),
                "coordinador_central": {"active": False}
            }
    
    # ==================== SISTEMA DE NOTIFICACIONES UNIFICADAS ====================
    
    async def _send_unified_notifications(self, notification_service: NotificationService, user_id: int, result: Dict[str, Any], accion: AccionUsuario) -> None:
        """
        Envía notificaciones unificadas basadas en el resultado del flujo ejecutado.
        Consolida múltiples tipos de notificaciones en un solo mensaje.
        
        Args:
            notification_service: Servicio de notificaciones
            user_id: ID del usuario
            result: Resultado del flujo ejecutado
            accion: Acción que se ejecutó
        """
        try:
            # Agregar notificación de puntos si se otorgaron
            if result.get("points_awarded"):
                await notification_service.add_notification(
                    user_id,
                    "points",
                    {
                        "points": result["points_awarded"],
                        "total": result.get("total_points", 0),
                        "source": accion.value
                    }
                )
            
            # Agregar notificaciones de misiones completadas si aplica
            if result.get("missions_completed"):
                for mission in result["missions_completed"]:
                    await notification_service.add_notification(
                        user_id,
                        "mission",
                        {
                            "name": mission["name"],
                            "points": mission["points"]
                        }
                    )
            
            # Agregar notificación de logro si aplica
            if result.get("achievement_unlocked"):
                await notification_service.add_notification(
                    user_id,
                    "achievement",
                    {
                        "name": result["achievement_unlocked"],
                        "description": result.get("achievement_description", "")
                    }
                )
            
            # Agregar notificación de insignia si aplica
            if result.get("badge_awarded"):
                await notification_service.add_notification(
                    user_id,
                    "badge",
                    {
                        "name": result["badge_awarded"],
                        "icon": result.get("badge_icon", "🏅")
                    }
                )
            
            # Agregar notificación de subida de nivel si aplica
            if result.get("level_up"):
                await notification_service.add_notification(
                    user_id,
                    "level",
                    {
                        "level": result["level_up"],
                        "reward": result.get("level_reward", "")
                    }
                )
            
            # Agregar notificación de pista desbloqueada si aplica
            if result.get("hint_unlocked"):
                await notification_service.add_notification(
                    user_id,
                    "hint",
                    {
                        "text": result["hint_unlocked"]
                    }
                )
            
            # Agregar notificación de la acción específica
            if accion == AccionUsuario.REACCIONAR_PUBLICACION:
                await notification_service.add_notification(
                    user_id,
                    "reaction",
                    {
                        "type": "publication",
                        "reaction_type": result.get("reaction_type", "unknown"),
                        "is_native": result.get("is_native_reaction", False)
                    }
                )
            elif accion == AccionUsuario.PARTICIPAR_CANAL:
                await notification_service.add_notification(
                    user_id,
                    "participation",
                    {
                        "action_type": result.get("action_type", "unknown"),
                        "points": result.get("points_awarded", 0)
                    }
                )
            elif accion == AccionUsuario.VERIFICAR_ENGAGEMENT:
                await notification_service.add_notification(
                    user_id,
                    "daily_check",
                    {
                        "streak": result.get("streak", 1),
                        "points": result.get("points_awarded", 0)
                    }
                )
            
            logger.debug(f"Sent unified notifications for {accion.value} to user {user_id}")
            
        except Exception as e:
            logger.exception(f"Error sending unified notifications: {e}")
            # Fallback: enviar mensaje básico
            try:
                basic_message = result.get("message", "Diana sonríe al ver tu progreso... 💋")
                await notification_service.send_immediate_notification(user_id, basic_message)
            except:
                pass  # Evitar loops de error
