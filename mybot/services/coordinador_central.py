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
    from .emotional_analysis_service import EmotionalAnalysisService
    from .character_voice_service import CharacterVoiceService, CharacterType, EmotionalContext
except ImportError:
    # Fallback to absolute imports for standalone usage
    from services.integration.channel_engagement_service import ChannelEngagementService
    from services.integration.narrative_point_service import NarrativePointService
    from services.integration.narrative_access_service import NarrativeAccessService
    from services.narrative_service import NarrativeService
    from services.point_service import PointService
    from services.emotional_analysis_service import EmotionalAnalysisService
    from services.character_voice_service import CharacterVoiceService, CharacterType, EmotionalContext

logger = logging.getLogger(__name__)

class AccionUsuario(enum.Enum):
    """Enumeración de acciones de usuario que pueden desencadenar flujos integrados."""
    REACCIONAR_PUBLICACION = "reaccionar_publicacion"
    ACCEDER_NARRATIVA_VIP = "acceder_narrativa_vip"
    TOMAR_DECISION = "tomar_decision"
    PARTICIPAR_CANAL = "participar_canal"
    VERIFICAR_ENGAGEMENT = "verificar_engagement"
    TEST_EVALUACION_EMOCIONAL = "test_evaluacion_emocional"

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
        # Servicio de análisis emocional (con graceful degradation)
        try:
            self.emotional_analysis = EmotionalAnalysisService(session)
        except Exception as e:
            logger.warning(f"EmotionalAnalysisService no disponible: {str(e)}")
            self.emotional_analysis = None
        
        # Servicio de voces de personajes (siempre disponible)
        self.character_voice = CharacterVoiceService()
    
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
            elif accion == AccionUsuario.TEST_EVALUACION_EMOCIONAL:
                return await self._flujo_test_evaluacion_emocional(user_id, **kwargs)
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
        # 1. Análisis emocional de timing de respuesta (no bloquea funcionalidad)
        emotional_context = None
        if self.emotional_analysis:
            try:
                import datetime
                emotional_context = await self.emotional_analysis.analyze_response_timing(
                    user_id, datetime.datetime.utcnow(), "reaction"
                )
            except Exception as e:
                logger.debug(f"Análisis emocional falló para usuario {user_id}: {str(e)}")
                # Graceful degradation - continuar sin análisis emocional
        
        # 2. Otorgar puntos por la reacción
        puntos_otorgados = await self.channel_engagement.award_channel_reaction(
            user_id, message_id, channel_id, bot=bot
        )
        
        if not puntos_otorgados:
            # Determinar contexto emocional para respuesta de fallo
            emotional_context_enum = self.character_voice.map_emotional_analysis_to_context(
                emotional_context, None, None, None
            )
            
            # Obtener respuesta auténtica de Lucien (custodio en situaciones de fallo)
            failure_message = self.character_voice.get_character_response(
                CharacterType.LUCIEN,
                emotional_context_enum,
                "reaction_failed",
                emotional_context
            )
            
            return {
                "success": False,
                "message": failure_message,
                "action": "reaction_failed",
                "emotional_context": emotional_context
            }
        
        # 3. Obtener puntos actuales del usuario
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
        
        # 5. Generar mensaje de respuesta con voces auténticas
        # Determinar contexto emocional y personaje apropiado
        user_history = {"total_interactions": puntos_actuales // 10}  # Aproximación basada en puntos
        emotional_context_enum = self.character_voice.map_emotional_analysis_to_context(
            emotional_context if emotional_context and emotional_context.get("success") else None,
            emotional_context,
            None,
            user_history
        )
        
        # Determinar qué personaje debe responder
        selected_character = self.character_voice.determine_character_from_emotional_context(
            emotional_context, "reaction_success", "high" if puntos_actuales > 100 else "moderate"
        )
        
        # Obtener respuesta auténtica del personaje seleccionado
        mensaje_autentico = self.character_voice.get_character_response(
            selected_character,
            emotional_context_enum,
            "reaction_success",
            emotional_context,
            user_history
        )
        
        # Agregar información de pista desbloqueada si existe
        if pista_desbloqueada:
            mensaje = f"{mensaje_autentico}\n\n*Nueva pista desbloqueada:* _{pista_desbloqueada}_"
        else:
            mensaje = mensaje_autentico
        
        # 6. Análisis de vulnerabilidad y mejoras contextuales (no afecta funcionalidad base)
        vulnerability_assessment = None
        response_enhancements = None
        