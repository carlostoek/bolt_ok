"""
Coordinador Central para orquestar la integración entre todos los módulos del sistema.
"""
import logging
import enum
import time
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from .integration.channel_engagement_service import ChannelEngagementService
    from .integration.narrative_point_service import NarrativePointService
    from .integration.narrative_access_service import NarrativeAccessService
    from .narrative_service import NarrativeService
    from .point_service import PointService
    from .user_archetype_service import UserArchetypeService
except ImportError:
    # Fallback to absolute imports for standalone usage
    from services.integration.channel_engagement_service import ChannelEngagementService
    from services.integration.narrative_point_service import NarrativePointService
    from services.integration.narrative_access_service import NarrativeAccessService
    from services.narrative_service import NarrativeService
    from services.point_service import PointService
    from services.user_archetype_service import UserArchetypeService

logger = logging.getLogger(__name__)

class AccionUsuario(enum.Enum):
    """Enumeración de acciones de usuario que pueden desencadenar flujos integrados."""
    REACCIONAR_PUBLICACION = "reaccionar_publicacion"
    ACCEDER_NARRATIVA_VIP = "acceder_narrativa_vip"
    TOMAR_DECISION = "tomar_decision"
    PARTICIPAR_CANAL = "participar_canal"
    VERIFICAR_ENGAGEMENT = "verificar_engagement"
    ANALIZAR_ARQUETIPO = "analizar_arquetipo"

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
        # Servicio de arquetipos de usuario
        self.archetype_service = UserArchetypeService(session)
        # Servicio de análisis emocional
        self.emotional_analysis = EmotionalAnalysisService(session)
    
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
            elif accion == AccionUsuario.ANALIZAR_ARQUETIPO:
                return await self._flujo_analizar_arquetipo(user_id, **kwargs)
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
        Flujo para manejar reacciones a publicaciones en canales con clasificación de arquetipos.
        
        Args:
            user_id: ID del usuario
            message_id: ID del mensaje al que se reaccionó
            channel_id: ID del canal donde está el mensaje
            reaction_type: Tipo de reacción (emoji)
            bot: Instancia del bot para enviar mensajes
            
        Returns:
            Dict con resultados y mensajes personalizados por arquetipo
        """
        # 1. Rastrear comportamiento para clasificación de arquetipo
        await self.archetype_service.track_behavioral_event(
            user_id, 
            "emotional_reaction", 
            {"reaction_type": reaction_type, "context": "channel_reaction"}
        )
        
        # 2. Otorgar puntos por la reacción
        puntos_otorgados = await self.channel_engagement.award_channel_reaction(
            user_id, message_id, channel_id, bot=bot
        )
        
        if not puntos_otorgados:
            # Personalizar mensaje de error basado en arquetipo
            error_message = await self.archetype_service.get_personalized_response(
                user_id, 
                "reaction", 
                "Diana observa tu gesto desde lejos, pero no parece haberlo notado... Intenta de nuevo más tarde."
            )
            return {
                "success": False,
                "message": error_message,
                "action": "reaction_failed"
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
        
        # 5. Generar mensaje personalizado basado en arquetipo
        mensaje_base = "Diana sonríe al notar tu reacción... *+10 besitos* 💋 han sido añadidos a tu cuenta."
        if pista_desbloqueada:
            mensaje_base = f"{mensaje_base}\n\n*Nueva pista desbloqueada:* _{pista_desbloqueada}_"
        
        # Personalizar mensaje según el arquetipo del usuario
        mensaje_personalizado = await self.archetype_service.get_personalized_response(
            user_id, "reaction", mensaje_base
        )
        
        return {
            "success": True,
            "message": mensaje_personalizado,
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
        Flujo para manejar decisiones narrativas del usuario con análisis de arquetipo.
        
        Args:
            user_id: ID del usuario
            decision_id: ID de la decisión tomada
            bot: Instancia del bot para enviar mensajes
            
        Returns:
            Dict con resultados y mensajes personalizados
        """
        # 1. Rastrear patrones de decisión para clasificación de arquetipo
        start_time = time.time()
        
        # 2. Procesar la decisión con verificación de puntos
        decision_result = await self.narrative_point.process_decision_with_points(user_id, decision_id, bot)
        
        # Calcular tiempo de respuesta para análisis de arquetipo
        response_time = time.time() - start_time
        
        # 3. Verificar resultado y rastrear comportamiento según el tipo
        if decision_result["type"] == "points_required":
            await self.archetype_service.track_behavioral_event(
                user_id, "analytical_pause", {"response_time": response_time, "context": "points_consideration"}
            )
            
            error_message = await self.archetype_service.get_personalized_response(
                user_id, 
                "narrative",
                "Diana suspira con anhelo...\n\n*\"Esta decisión requiere más besitos de los que tienes ahora, mi amor. Algunas fantasías necesitan más... intensidad.\"*\n\nNecesitas más besitos para esta elección. Participa en los canales para conseguir más."
            )
            
            return {
                "success": False,
                "message": error_message,
                "action": "points_required",
                "decision_id": decision_id
            }
            
        elif decision_result["type"] == "error":
            await self.archetype_service.track_behavioral_event(
                user_id, "reflective_pause", {"response_time": response_time, "context": "decision_error"}
            )
            
            error_message = await self.archetype_service.get_personalized_response(
                user_id,
                "narrative", 
                "Diana parece confundida por tu elección...\n\n*\"No logro entender lo que deseas, mi amor. ¿Podrías intentarlo de nuevo?\"*"
            )
            
            return {
                "success": False,
                "message": error_message,
                "action": "decision_error",
                "error": decision_result["message"]
            }
        
        # 4. Análisis emocional de la decisión
        interaction_data = {
            "response_time": response_time,
            "interaction_type": "decision",
            "content": decision_content,
            "fragment_key": decision_result.get("fragment", {}).get("key"),
            "context": {"decision_id": decision_id}
        }
        
        # Realizar análisis emocional en paralelo con arquetipo
        emotional_analysis = await self.emotional_analysis.analyze_interaction(
            user_id, interaction_data
        )
        
        # 5. Decisión exitosa - determinar tipo de decisión para arquetipo
        decision_type = "quick_decision" if response_time < 5 else "thoughtful_decision"
        
        # Análisis adicional basado en el contenido de la decisión
        decision_content = decision_result.get("decision_content", "")
        if any(word in decision_content.lower() for word in ["poetic", "metaphor", "beauty", "aesthetic"]):
            decision_type = "aesthetic_preference"
        elif any(word in decision_content.lower() for word in ["analyze", "understand", "reflect", "consider"]):
            decision_type = "systematic_navigation"
        elif any(word in decision_content.lower() for word in ["explore", "detail", "deeper", "more"]):
            decision_type = "detailed_exploration"
        
        await self.archetype_service.track_behavioral_event(
            user_id, decision_type, {"response_time": response_time, "context": "narrative_decision"}
        )
        
        # 6. Personalizar mensaje de éxito según arquetipo y análisis emocional
        base_message = "Diana asiente con una sonrisa seductora mientras la historia toma un nuevo rumbo..."
        personalized_message = await self.archetype_service.get_personalized_response(
            user_id, "narrative", base_message
        )
        
        # Enriquecer respuesta con insights emocionales si están disponibles
        if emotional_analysis.get("success") and emotional_analysis.get("recommendations"):
            logger.debug(f"Emotional insights for user {user_id}: {emotional_analysis['recommendations']}")
        
        return {
            "success": True,
            "message": personalized_message,
            "fragment": decision_result["fragment"],
            "action": "decision_success",
            "decision_type": decision_type,
            "emotional_analysis": {
                "response_type": emotional_analysis.get("response_type"),
                "vulnerability_level": emotional_analysis.get("profile_update", {}).get("vulnerability_level"),
                "analysis_time_ms": emotional_analysis.get("analysis_time_ms", 0)
            } if emotional_analysis.get("success") else None
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
    
    async def _flujo_analizar_arquetipo(self, user_id: int, bot=None) -> Dict[str, Any]:
        """
        Flujo para análisis y clasificación de arquetipo de usuario.
        
        Args:
            user_id: ID del usuario
            bot: Instancia del bot para enviar mensajes
            
        Returns:
            Dict con análisis de arquetipo y recomendaciones personalizadas
        """
        try:
            # 1. Obtener clasificación actual del arquetipo
            archetype, confidence = await self.archetype_service.get_user_archetype(user_id)
            
            # 2. Obtener análisis completo
            analytics = await self.archetype_service.get_archetype_analytics(user_id)
            
            # 3. Generar mensaje personalizado según el arquetipo detectado
            archetype_descriptions = {
                "explorador_profundo": "Eres un alma curiosa que busca los secretos más profundos de cada historia. Tu paciencia y atención al detalle te revelan misterios que otros pasan por alto.",
                "directo_autentico": "Tu autenticidad y franqueza son tu fortaleza. Vas directo al corazón de las emociones sin rodeos, creando conexiones profundas y genuinas.",
                "poeta_deseo": "Posees un alma poética que encuentra belleza en cada metáfora. Tu sensibilidad estética te permite apreciar los matices más sutiles del arte del deseo.",
                "analitico_empatico": "Tu mente analítica combinada con tu corazón empático te permite comprender tanto la lógica como la emoción de cada situación con gran profundidad.",
                "persistente_paciente": "Tu constancia y paciencia son admirables. Sabes que las mejores experiencias requieren tiempo y dedicación, y nunca te rindes."
            }
            
            archetype_name = archetype.value if hasattr(archetype, 'value') else str(archetype)
            description = archetype_descriptions.get(archetype_name, "Tu personalidad única está siendo analizada por Diana...")
            
            # 4. Personalizar mensaje usando el servicio de arquetipos
            base_message = f"Diana te observa con una mirada penetrante, leyendo los secretos de tu alma...\n\n*\"Tu arquetipo es: {archetype_name.replace('_', ' ').title()}\"*\n\n{description}\n\n*Confianza en la clasificación: {confidence:.1%}*"
            
            personalized_message = await self.archetype_service.get_personalized_response(
                user_id, "analysis", base_message
            )
            
            # 5. Agregar recomendaciones si hay suficientes datos
            recommendations = []
            if analytics.get('classification_count', 0) > 5:
                if confidence < 0.7:
                    recommendations.append("Continúa interactuando para que Diana pueda conocerte mejor.")
                if archetype_name == "explorador_profundo":
                    recommendations.append("Explora los fragmentos narrativos ocultos para descubrir secretos especiales.")
                elif archetype_name == "directo_autentico":
                    recommendations.append("Tus respuestas rápidas y honestas son valoradas. Mantén esa autenticidad.")
                elif archetype_name == "poeta_deseo":
                    recommendations.append("Busca las opciones más poéticas en la narrativa para experiencias únicas.")
                elif archetype_name == "analitico_empatico":
                    recommendations.append("Tus análisis profundos pueden desbloquear contenido especial.")
                elif archetype_name == "persistente_paciente":
                    recommendations.append("Tu paciencia será recompensada con contenido exclusivo por lealtad.")
            
            if recommendations:
                personalized_message += f"\n\n*Recomendaciones personalizadas:*\n• " + "\n• ".join(recommendations)
            
            return {
                "success": True,
                "message": personalized_message,
                "archetype": archetype_name,
                "confidence": confidence,
                "analytics": analytics,
                "action": "archetype_analysis_success"
            }
            
        except Exception as e:
            logger.error(f"Error en análisis de arquetipo para usuario {user_id}: {e}")
            return {
                "success": False,
                "message": "Diana parece confundida al intentar leer tu alma... Inténtalo de nuevo más tarde.",
                "action": "archetype_analysis_error",
                "error": str(e)
            }
