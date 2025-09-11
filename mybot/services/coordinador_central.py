"""
Coordinador Central para orquestar la integración entre todos los módulos del sistema.
"""
import logging
import enum
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from .integration.channel_engagement_service import ChannelEngagementService
    from .integration.narrative_point_service import NarrativePointService
    from .integration.narrative_access_service import NarrativeAccessService
    from .narrative_service import NarrativeService
    from .point_service import PointService
except ImportError:
    # Fallback to absolute imports for standalone usage
    from services.integration.channel_engagement_service import ChannelEngagementService
    from services.integration.narrative_point_service import NarrativePointService
    from services.integration.narrative_access_service import NarrativeAccessService
    from services.narrative_service import NarrativeService
    from services.point_service import PointService

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
        # Servicios base
        self.narrative_service = NarrativeService(session)
        self.point_service = PointService(session)
    
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
            # Seleccionar el flujo adecuado según la acción
            if accion == AccionUsuario.REACCIONAR_PUBLICACION:
                return await self._flujo_reaccion_publicacion(user_id, **kwargs)
            elif accion == AccionUsuario.ACCEDER_NARRATIVA_VIP:
                return await self._flujo_acceso_narrativa_vip(user_id, **kwargs)
            elif accion == AccionUsuario.TOMAR_DECISION:
                return await self._flujo_tomar_decision(user_id, **kwargs)
            elif accion == AccionUsuario.PARTICIPAR_CANAL:
                return await self._flujo_participacion_canal(user_id, **kwargs)
            elif accion == AccionUsuario.VERIFICAR_ENGAGEMENT:
                return await self._flujo_verificar_engagement(user_id, **kwargs)
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
            user_id, message_id, channel_id, bot=bot
        )
        
        if not puntos_otorgados:
            return {
                "success": False,
                "message": "Diana observa tu gesto desde lejos, pero no parece haberlo notado... Intenta de nuevo más tarde.",
                "action": "reaction_failed"
            }
        
        # 2. Obtener puntos actuales del usuario
        puntos_actuales = await self.point_service.get_user_points(user_id)
        
        # 3. Verificar si se desbloquea una pista narrativa
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
        
        # 4. Generar mensaje de respuesta
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
        user_progress = await self.point_service.get_user_progress(user_id)
        streak = user_progress.checkin_streak if user_progress else 1
        
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
