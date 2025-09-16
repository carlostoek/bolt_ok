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
    ACCEDER_TIENDA = "acceder_tienda"
    COMPRAR_ITEM = "comprar_item"
    AGREGAR_A_MOCHILA = "agregar_a_mochila"
    VERIFICAR_ACCESO_NIVEL = "verificar_acceso_nivel"
    ACCEDER_LORE = "acceder_lore"
    ADMIN_SHOP_OPERATION = "admin_shop_operation"
    ADMIN_NARRATIVE_OPERATION = "admin_narrative_operation"
    ADMIN_LORE_OPERATION = "admin_lore_operation"

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
            elif accion == AccionUsuario.ACCEDER_TIENDA:
                return await self._flujo_acceder_tienda(user_id, **kwargs)
            elif accion == AccionUsuario.COMPRAR_ITEM:
                return await self._flujo_comprar_item(user_id, **kwargs)
            elif accion == AccionUsuario.AGREGAR_A_MOCHILA:
                return await self._flujo_agregar_a_mochila(user_id, **kwargs)
            elif accion == AccionUsuario.VERIFICAR_ACCESO_NIVEL:
                return await self._flujo_verificar_acceso_nivel(user_id, **kwargs)
            elif accion == AccionUsuario.ACCEDER_LORE:
                return await self._flujo_acceder_lore(user_id, **kwargs)
            elif accion == AccionUsuario.ADMIN_SHOP_OPERATION:
                return await self._flujo_admin_shop_operation(user_id, **kwargs)
            elif accion == AccionUsuario.ADMIN_NARRATIVE_OPERATION:
                return await self._flujo_admin_narrative_operation(user_id, **kwargs)
            elif accion == AccionUsuario.ADMIN_LORE_OPERATION:
                return await self._flujo_admin_lore_operation(user_id, **kwargs)
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
        if self.emotional_analysis:
            try:
                # Evaluar vulnerabilidad emocional
                vulnerability_assessment = await self.emotional_analysis.assess_vulnerability_level(
                    user_id, reaction_type, {"action": "reaction", "channel_id": channel_id}
                )
                
                # Generar mejoras contextuales (solo sugerencias, no modifican respuesta)
                base_response = {
                    "message": mensaje,
                    "type": "reaction_success",
                    "points": 10
                }
                response_enhancements = await self.emotional_analysis.generate_contextual_response_enhancement(
                    user_id, base_response, emotional_context
                )
            except Exception as e:
                logger.debug(f"Análisis de vulnerabilidad/mejoras falló para usuario {user_id}: {str(e)}")
                # Graceful degradation
        
        return {
            "success": True,
            "message": mensaje,
            "points_awarded": 10,
            "total_points": puntos_actuales,
            "hint_unlocked": pista_desbloqueada,
            "action": "reaction_success",
            # Información adicional de análisis emocional (no afecta funcionalidad existente)
            "emotional_context": emotional_context,
            "vulnerability_assessment": vulnerability_assessment,
            "response_enhancements": response_enhancements
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
        
        # 2. Procesar resultado con voces auténticas
        if isinstance(fragment_result, dict) and fragment_result.get("type") == "subscription_required":
            # Diana maneja restricciones VIP con su concepto de intimidad
            vip_message = self.character_voice.get_character_response(
                CharacterType.DIANA,
                EmotionalContext.VULNERABILIDAD_BAJA,  # Usuario no ha alcanzado nivel VIP aún
                "vip_required"
            )
            
            return {
                "success": False,
                "message": f"{vip_message}\n\nUsa /vip para acceder a contenido exclusivo.",
                "action": "vip_required",
                "fragment_key": fragment_key
            }
        
        # 3. Acceso permitido con voz auténtica
        # Diana guía hacia contenido VIP con intimidad profunda
        access_message = self.character_voice.get_character_response(
            CharacterType.DIANA,
            EmotionalContext.USUARIO_AVANZADO,  # Usuario con acceso VIP es avanzado
            "vip_access_granted"
        )
        
        return {
            "success": True,
            "message": access_message,
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
        # Define which decisions require which items
        decision_requirements = {
            1: "📖 Diario Secreto",  # First decision requires the diary
            15: "📓 Diario Íntimo",  # Diary intimate choice requires the intimate diary
            # Add more decision IDs and their required items here
        }
        
        # Check if this decision requires an item
        required_item = decision_requirements.get(decision_id)
        if required_item:
            from services.shop_service import ShopService
            shop_service = ShopService(self.session)
            has_item = await shop_service.has_item_in_inventory(user_id, required_item)
            
            if not has_item:
                # For diary intimate decision, redirect to teaser fragment instead of blocking
                if decision_id == 15:  # Diary intimate decision
                    # Process decision to teaser fragment instead
                    teaser_fragment = await self.narrative_service._get_fragment_by_key("diana_diary_tease")
                    if teaser_fragment:
                        # Update user state to teaser fragment
                        user_state = await self.narrative_service._get_or_create_user_state(user_id)
                        user_state.current_fragment_key = teaser_fragment.key
                        user_state.fragments_visited = (user_state.fragments_visited or 0) + 1
                        await self.narrative_service._process_fragment_rewards(user_id, teaser_fragment)
                        await self.session.commit()

                        return {
                            "success": True,
                            "fragment": teaser_fragment,
                            "action": "decision_success"
                        }

                # For other items, show restriction message
                try:
                    restriction_message = self.character_voice.get_character_response(
                        CharacterType.DIANA,
                        EmotionalContext.VULNERABILIDAD_BAJA,
                        "item_required"
                    )
                except:
                    restriction_message = "💋 Diana susurra: 'Este camino requiere algo más íntimo...'"

                return {
                    "success": False,
                    "message": f"{restriction_message}\n\n🔒 **Acceso Restringido**\n\nNecesitas el {required_item} para tomar esta decisión.\n\nVisita la tienda para adquirirlo.",
                    "action": "item_required",
                    "decision_id": decision_id,
                    "required_item": required_item
                }
        
        # 1. Análisis emocional previo a la decisión (no bloquea funcionalidad)
        emotional_context = None
        behavioral_patterns = None
        if self.emotional_analysis:
            try:
                import datetime
                # Analizar timing de la decisión
                emotional_context = await self.emotional_analysis.analyze_response_timing(
                    user_id, datetime.datetime.utcnow(), "decision"
                )
                
                # Detectar patrones de comportamiento para decisiones
                recent_actions = [{"timestamp": datetime.datetime.utcnow(), "type": "decision", "id": decision_id}]
                behavioral_patterns = await self.emotional_analysis.detect_behavioral_patterns(
                    user_id, recent_actions
                )
            except Exception as e:
                logger.debug(f"Análisis emocional de decisión falló para usuario {user_id}: {str(e)}")
                # Graceful degradation
        
        # 2. Procesar la decisión con verificación de puntos
        decision_result = await self.narrative_point.process_decision_with_points(user_id, decision_id, bot)
        
        # 3. Verificar resultado con voces auténticas
        if decision_result["type"] == "points_required":
            # Determinar contexto emocional para falta de puntos
            emotional_context_enum = self.character_voice.map_emotional_analysis_to_context(
                emotional_context, None, behavioral_patterns, None
            )
            
            # Diana responde con anhelo cuando faltan puntos
            points_message = self.character_voice.get_character_response(
                CharacterType.DIANA,
                emotional_context_enum,
                "points_required",
                emotional_context
            )
            
            return {
                "success": False,
                "message": points_message,
                "action": "points_required",
                "decision_id": decision_id
            }
        elif decision_result["type"] == "error":
            # Lucien maneja errores de sistema como custodio
            error_message = self.character_voice.get_character_response(
                CharacterType.LUCIEN,
                EmotionalContext.PAUSA_REFLEXIVA,
                "decision_error",
                emotional_context
            )
            
            return {
                "success": False,
                "message": error_message,
                "action": "decision_error",
                "error": decision_result["message"]
            }
        
        # 4. Análisis emocional post-decisión y tracking de evolución
        vulnerability_assessment = None
        emotional_evolution = None
        if self.emotional_analysis:
            try:
                # Evaluar vulnerabilidad después de la decisión exitosa
                vulnerability_assessment = await self.emotional_analysis.assess_vulnerability_level(
                    user_id, str(decision_id), {"action": "decision_success", "fragment": decision_result["fragment"]}
                )
                
                # Rastrear evolución emocional (últimos 7 días)
                emotional_evolution = await self.emotional_analysis.track_emotional_evolution(user_id, 7)
                
            except Exception as e:
                logger.debug(f"Análisis post-decisión falló para usuario {user_id}: {str(e)}")
                # Graceful degradation
        
        # 5. Decisión exitosa
        # Para decisiones especiales (como las de items), no agregar mensaje extra
        # ya que el flujo narrativo debe ser limpio
        special_decision_ids = {15}  # Diary intimate decision

        if decision_id in special_decision_ids:
            # Para decisiones especiales, retornar solo el fragmento
            return {
                "success": True,
                "fragment": decision_result["fragment"],
                "action": "decision_success",
                # Información adicional de análisis emocional
                "emotional_context": emotional_context,
                "behavioral_patterns": behavioral_patterns,
                "vulnerability_assessment": vulnerability_assessment,
                "emotional_evolution": emotional_evolution
            }
        else:
            # Para decisiones normales, incluir voz auténtica
            # Determinar contexto emocional para éxito
            user_points = await self.point_service.get_user_points(user_id)
            user_history = {"total_interactions": user_points // 10}
            emotional_context_enum = self.character_voice.map_emotional_analysis_to_context(
                emotional_context, emotional_context, behavioral_patterns, user_history
            )

            # Diana siempre responde a decisiones exitosas (momentos íntimos)
            success_message = self.character_voice.get_character_response(
                CharacterType.DIANA,
                emotional_context_enum,
                "decision_success",
                emotional_context,
                user_history
            )

            return {
                "success": True,
                "message": success_message,
                "fragment": decision_result["fragment"],
                "action": "decision_success",
                # Información adicional de análisis emocional
                "emotional_context": emotional_context,
                "behavioral_patterns": behavioral_patterns,
                "vulnerability_assessment": vulnerability_assessment,
                "emotional_evolution": emotional_evolution
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
        # 1. Análisis emocional de participación en canal (no bloquea funcionalidad)
        emotional_context = None
        if self.emotional_analysis:
            try:
                import datetime
                # Analizar timing y patrones de participación
                emotional_context = await self.emotional_analysis.analyze_response_timing(
                    user_id, datetime.datetime.utcnow(), f"channel_participation_{action_type}"
                )
            except Exception as e:
                logger.debug(f"Análisis emocional de participación falló para usuario {user_id}: {str(e)}")
                # Graceful degradation
        
        # 2. Otorgar puntos por participación
        participacion_exitosa = await self.channel_engagement.award_channel_participation(
            user_id, channel_id, action_type, bot
        )
        
        if not participacion_exitosa:
            # Lucien maneja fallos de participación como custodio
            participation_fail_message = self.character_voice.get_character_response(
                CharacterType.LUCIEN,
                EmotionalContext.PAUSA_REFLEXIVA,
                "participation_failed",
                emotional_context
            )
            
            return {
                "success": False,
                "message": participation_fail_message,
                "action": "participation_failed",
                "emotional_context": emotional_context
            }
        
        # 3. Determinar puntos otorgados según el tipo de acción
        puntos = 5 if action_type == "post" else 2 if action_type == "comment" else 1
        
        # 4. Generar mensaje con voz auténtica según tipo de acción
        user_points = await self.point_service.get_user_points(user_id)
        user_history = {"total_interactions": user_points // 5}  # Aproximación
        
        emotional_context_enum = self.character_voice.map_emotional_analysis_to_context(
            emotional_context, emotional_context, None, user_history
        )
        
        # Diana responde a participación social (conexión)
        base_message = self.character_voice.get_character_response(
            CharacterType.DIANA,
            emotional_context_enum,
            f"participation_{action_type}",
            emotional_context,
            user_history
        )
        
        # Agregar puntos según acción
        points_text = f"\n\n*+{puntos} besito{'s' if puntos > 1 else ''}* 💋 por tu {action_type}."
        mensaje = f"{base_message}{points_text}"
        
        # 5. Análisis emocional post-participación y mejoras contextuales
        behavioral_patterns = None
        response_enhancements = None
        if self.emotional_analysis:
            try:
                import datetime
                # Detectar patrones de participación social
                recent_actions = [{"timestamp": datetime.datetime.utcnow(), "type": "channel_participation", "action_type": action_type, "channel_id": channel_id}]
                behavioral_patterns = await self.emotional_analysis.detect_behavioral_patterns(
                    user_id, recent_actions
                )
                
                # Generar mejoras contextuales
                base_response = {"message": mensaje, "type": "participation_success", "points": puntos}
                response_enhancements = await self.emotional_analysis.generate_contextual_response_enhancement(
                    user_id, base_response, emotional_context
                )
            except Exception as e:
                logger.debug(f"Análisis post-participación falló para usuario {user_id}: {str(e)}")
                # Graceful degradation
        
        return {
            "success": True,
            "message": mensaje,
            "points_awarded": puntos,
            "action": "participation_success",
            "action_type": action_type,
            # Información adicional de análisis emocional
            "emotional_context": emotional_context,
            "behavioral_patterns": behavioral_patterns,
            "response_enhancements": response_enhancements
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
            # Diana maneja la paciencia con su concepto de timing
            patience_message = self.character_voice.get_character_response(
                CharacterType.DIANA,
                EmotionalContext.PAUSA_REFLEXIVA,
                "daily_already_done"
            )
            
            return {
                "success": False,
                "message": patience_message,
                "action": "daily_check_already_done"
            }
        
        # 2. Obtener información de progreso
        user_progress = await self.point_service.get_user_progress(user_id)
        streak = user_progress.checkin_streak if user_progress else 1
        
        # 3. Generar mensaje con voz auténtica según racha
        user_history = {"streak": streak, "total_interactions": streak * 2}  # Aproximación
        
        if streak % 7 == 0:  # Racha semanal - alta dedicación
            weekly_message = self.character_voice.get_character_response(
                CharacterType.DIANA,
                EmotionalContext.ENGAGEMENT_ALTO,
                "weekly_streak",
                None,
                user_history
            )
            mensaje = f"{weekly_message}\n\n*+25 besitos* 💋 por tu constancia semanal."
        else:
            daily_message = self.character_voice.get_character_response(
                CharacterType.DIANA,
                EmotionalContext.USUARIO_AVANZADO if streak > 7 else EmotionalContext.NUEVO_USUARIO,
                "daily_check",
                None,
                user_history
            )
            mensaje = f"{daily_message}\n\n*+10 besitos* 💋 por tu visita diaria."
        
        return {
            "success": True,
            "message": mensaje,
            "streak": streak,
            "points_awarded": 25 if streak % 7 == 0 else 10,
            "action": "daily_check_success"
        }
    
    async def _flujo_acceder_tienda(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """
        Flujo para acceder a la tienda y listar artículos disponibles.
        """
        try:
            # Import here to avoid circular imports
            from services.shop_service import ShopService
            
            shop_service = ShopService(self.session)
            items = await shop_service.get_available_items(user_id)
            
            # Convert items to a list of dictionaries to ensure they're serializable
            # and can be used in the keyboard builder
            items_data = []
            for item in items:
                items_data.append({
                    'id': item.id,
                    'name': item.name,
                    'price': item.price,
                    'is_vip_only': item.is_vip_only
                })
            
            return {
                "success": True,
                "action": "shop_access",
                "items": items_data
            }
        except Exception as e:
            logger.exception(f"Error en flujo de tienda para usuario {user_id}: {str(e)}")
            return {
                "success": False,
                "message": "Error al acceder a la tienda. Intenta nuevamente.",
                "error": str(e)
            }

    async def _flujo_comprar_item(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """
        Flujo para comprar un item de la tienda.
        """
        try:
            item_id = kwargs.get("item_id")
            if not item_id:
                return {
                    "success": False,
                    "message": "ID de artículo no proporcionado."
                }
            
            # Import here to avoid circular imports
            from services.shop_service import ShopService
            
            shop_service = ShopService(self.session)
            result = await shop_service.purchase_item(user_id, int(item_id))
            
            return result
        except ValueError:
            return {
                "success": False,
                "message": "ID de artículo inválido."
            }
        except Exception as e:
            logger.exception(f"Error en compra para usuario {user_id}: {str(e)}")
            return {
                "success": False,
                "message": "Error durante la compra. Intenta nuevamente.",
                "error": str(e)
            }


    async def _flujo_verificar_acceso_nivel(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """
        Flujo para verificar si el usuario puede acceder a un nivel específico.
        """
        try:
            level_name = kwargs.get("level_name")
            if not level_name:
                return {
                    "success": False,
                    "message": "Nombre del nivel no proporcionado."
                }
            
            # Check access based on level name
            if level_name == "nivel_muestra":
                # Import here to avoid circular imports
                from services.shop_service import ShopService
                shop_service = ShopService(self.session)
                has_diario = await shop_service.has_item_in_inventory(user_id, "📖 Diario Secreto")
                
                if has_diario:
                    return {
                        "success": True,
                        "message": "Acceso concedido al nivel de muestra.",
                        "access_granted": True
                    }
                else:
                    return {
                        "success": False,
                        "message": "Necesitas el 📖 Diario Secreto de Diana para acceder a este nivel.\n\nVisita la tienda para adquirirlo.",
                        "access_granted": False
                    }
            elif level_name == "diario_intimo":
                # Check for the "Diario Íntimo" item for the intimate narrative level
                from services.shop_service import ShopService
                shop_service = ShopService(self.session)
                has_diario_intimo = await shop_service.has_item_in_inventory(user_id, "📓 Diario Íntimo")

                if has_diario_intimo:
                    return {
                        "success": True,
                        "message": "🔓 **Nivel Desbloqueado: Diario Íntimo**\n\n💫 *El diario más personal de Diana se abre ante ti...*\n\n✨ Sus pensamientos más profundos, sus deseos secretos y confesiones íntimas ahora son tuyos.",
                        "access_granted": True
                    }
                else:
                    return {
                        "success": False,
                        "message": "❌ **Acceso Restringido**\n\n💋 *Diana susurra: 'Mi diario más íntimo requiere una conexión especial...'*\n\nNecesitas el **📓 Diario Íntimo** (30 besitos) de la tienda para acceder a este contenido exclusivo.",
                        "access_granted": False
                    }
            else:
                return {
                    "success": False,
                    "message": f"Nivel '{level_name}' no reconocido."
                }
        except Exception as e:
            logger.exception(f"Error verificando acceso para usuario {user_id}: {str(e)}")
            return {
                "success": False,
                "message": "Error al verificar el acceso al nivel.",
                "error": str(e)
            }

    async def _flujo_acceder_lore(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """
        Flujo para acceder a contenido lore desbloqueado desde el inventario.

        Args:
            user_id: ID del usuario de Telegram
            **kwargs: Debe contener lore_piece_id

        Returns:
            Dict con resultado del acceso al lore
        """
        try:
            lore_piece_id = kwargs.get("lore_piece_id")
            if not lore_piece_id:
                return {
                    "success": False,
                    "message": "ID de lore no proporcionado."
                }

            # Verificar que el usuario tiene acceso al lore piece
            from database.models import UserLorePiece, LorePiece
            from sqlalchemy import select

            # Check if user has this lore piece in their collection
            user_lore_stmt = select(UserLorePiece).where(
                UserLorePiece.user_id == user_id,
                UserLorePiece.lore_piece_id == lore_piece_id
            )
            user_lore_result = await self.session.execute(user_lore_stmt)
            user_lore = user_lore_result.scalar_one_or_none()

            if not user_lore:
                return {
                    "success": False,
                    "message": "No tienes acceso a este contenido. Debe ser desbloqueado primero."
                }

            # Get the lore piece content
            lore_stmt = select(LorePiece).where(LorePiece.id == lore_piece_id)
            lore_result = await self.session.execute(lore_stmt)
            lore_piece = lore_result.scalar_one_or_none()

            if not lore_piece:
                return {
                    "success": False,
                    "message": "Contenido no encontrado."
                }

            # Update the access timestamp if this is not the first access
            if not user_lore.unlocked_at:
                from datetime import datetime
                user_lore.unlocked_at = datetime.utcnow()
                await self.session.commit()

            # Use narrative service to display the lore content
            display_result = await self.narrative_service.display_lore_piece(user_id, lore_piece)

            if display_result["success"]:
                # Generate character response based on lore content
                character_response = None
                if self.character_voice:
                    # Determine which character should respond based on lore content
                    if "diana" in lore_piece.title.lower() or "íntimo" in lore_piece.title.lower():
                        character_type = CharacterType.DIANA
                        emotional_context = EmotionalContext.INTIMIDAD_PROFUNDA
                    else:
                        character_type = CharacterType.LUCIEN
                        emotional_context = EmotionalContext.PRESENTACION_CONTENIDO

                    character_response = self.character_voice.get_character_response(
                        character_type,
                        emotional_context,
                        "lore_access_success",
                        {"lore_title": lore_piece.title}
                    )

                return {
                    "success": True,
                    "message": "Contenido accedido exitosamente.",
                    "lore_content": {
                        "id": lore_piece.id,
                        "title": lore_piece.title,
                        "content": lore_piece.content,
                        "content_type": lore_piece.content_type,
                        "category": lore_piece.category
                    },
                    "character_response": character_response,
                    "display_result": display_result
                }
            else:
                return {
                    "success": False,
                    "message": f"Error al mostrar el contenido: {display_result.get('message', 'Error desconocido')}"
                }

        except Exception as e:
            logger.exception(f"Error accediendo al lore {lore_piece_id} para usuario {user_id}: {str(e)}")
            return {
                "success": False,
                "message": "Error interno al acceder al contenido.",
                "error": str(e)
            }

    async def _flujo_test_evaluacion_emocional(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """
        Flujo para ejecutar el test de evaluación emocional aislado.
        
        Args:
            user_id: ID del usuario
            **kwargs: Parámetros del test (action_type, response_time, option_selected)
            
        Returns:
            Dict con resultados del análisis emocional y perfil del usuario
        """
        try:
            import datetime
            
            action_type = kwargs.get("action_type", "start_test")
            
            if action_type == "start_test":
                # Inicializar el test - retornar mensaje de bienvenida
                welcome_message = self.character_voice.get_character_response(
                    CharacterType.DIANA,
                    EmotionalContext.NUEVO_USUARIO,
                    "test_evaluation_start"
                ) if self.character_voice else "¡Descubre tu perfil emocional!"
                
                return {
                    "success": True,
                    "action": "test_started",
                    "message": welcome_message,
                    "test_active": True
                }
            
            elif action_type == "process_response":
                # Procesar respuesta del usuario con análisis de timing
                response_time = kwargs.get("response_time", 0)  # En segundos
                option_selected = kwargs.get("option_selected", "unknown")
                
                # Realizar análisis emocional del timing de respuesta
                emotional_context = None
                if self.emotional_analysis:
                    try:
                        # Usar el servicio de análisis emocional para evaluar timing
                        emotional_context = await self.emotional_analysis.analyze_response_timing(
                            user_id, datetime.datetime.utcnow(), "test_evaluation"
                        )
                    except Exception as e:
                        logger.debug(f"Análisis emocional de test falló para usuario {user_id}: {str(e)}")
                
                # Clasificar usuario según timing de respuesta
                user_type = self._classify_user_by_response_time(response_time)
                
                # Evaluación de vulnerabilidad específica para el test
                vulnerability_assessment = None
                if self.emotional_analysis:
                    try:
                        vulnerability_assessment = await self.emotional_analysis.assess_vulnerability_level(
                            user_id, option_selected, {
                                "action": "test_evaluation", 
                                "response_time": response_time,
                                "option": option_selected
                            }
                        )
                    except Exception as e:
                        logger.debug(f"Evaluación de vulnerabilidad de test falló para usuario {user_id}: {str(e)}")
                
                # Determinar contexto emocional para la respuesta
                emotional_context_enum = self.character_voice.map_emotional_analysis_to_context(
                    emotional_context, emotional_context, None, {"response_time": response_time}
                ) if self.character_voice else EmotionalContext.PAUSA_REFLEXIVA
                
                # Generar mensaje personalizado según el perfil detectado
                profile_message = self._generate_profile_message(
                    user_type, emotional_context, vulnerability_assessment
                )
                
                # Respuesta auténtica del personaje según el perfil
                character_response = self.character_voice.get_character_response(
                    CharacterType.DIANA,
                    emotional_context_enum,
                    f"test_result_{user_type}",
                    emotional_context
                ) if self.character_voice else profile_message
                
                return {
                    "success": True,
                    "action": "test_completed",
                    "message": f"{character_response}\n\n{profile_message}",
                    "user_type": user_type,
                    "response_time": response_time,
                    "option_selected": option_selected,
                    "emotional_context": emotional_context,
                    "vulnerability_assessment": vulnerability_assessment
                }
            
            else:
                return {
                    "success": False,
                    "message": "Tipo de acción no reconocido para el test emocional."
                }
                
        except Exception as e:
            logger.exception(f"Error en flujo de test emocional para usuario {user_id}: {str(e)}")
            return {
                "success": False,
                "message": "Error durante el test emocional. Intenta nuevamente.",
                "error": str(e)
            }
    
    def _classify_user_by_response_time(self, response_time: float) -> str:
        """
        Clasifica al usuario según su tiempo de respuesta en el test.
        
        Args:
            response_time: Tiempo de respuesta en segundos
            
        Returns:
            String con el tipo de usuario detectado
        """
        if response_time < 3:
            return "impulso_autentico"
        elif response_time <= 15:
            return "pausa_reflexiva"
        elif response_time <= 60:
            return "contemplacion"
        else:
            return "abandono"
    
    def _generate_profile_message(
        self, 
        user_type: str, 
        emotional_context: Dict[str, Any] = None,
        vulnerability_assessment: Dict[str, Any] = None
    ) -> str:
        """
        Genera mensaje personalizado del perfil emocional detectado.
        
        Args:
            user_type: Tipo de usuario clasificado
            emotional_context: Contexto emocional del análisis
            vulnerability_assessment: Evaluación de vulnerabilidad
            
        Returns:
            String con el mensaje personalizado del perfil
        """
        profile_messages = {
            "impulso_autentico": (
                "🔥 **IMPULSO AUTÉNTICO**\n\n"
                "Respondes desde el corazón, sin filtros. Tu naturaleza espontánea "
                "te lleva a conectar de manera genuina y directa. Eres de quienes "
                "viven el momento con intensidad."
            ),
            "pausa_reflexiva": (
                "💭 **PAUSA REFLEXIVA**\n\n"
                "Tomas tiempo para procesar antes de responder. Esta cualidad te "
                "permite tomar decisiones más conscientes y conectar de manera "
                "profunda con tus emociones."
            ),
            "contemplacion": (
                "🌙 **CONTEMPLACIÓN**\n\n"
                "Tu mente busca comprender profundamente antes de actuar. Este "
                "enfoque reflexivo te permite acceder a capas más profundas de "
                "comprensión y conexión emocional."
            ),
            "abandono": (
                "🌊 **ABANDONO**\n\n"
                "Tiendes a alejarte cuando sientes presión. Esto puede indicar "
                "que necesitas espacios seguros para explorar y conectar a tu "
                "propio ritmo, sin prisas."
            )
        }
        
        base_message = profile_messages.get(user_type, profile_messages["pausa_reflexiva"])
        
        # Agregar insights adicionales basados en el análisis emocional
        if emotional_context and emotional_context.get("success"):
            timing_pattern = emotional_context.get("timing_pattern", "normal")
            if timing_pattern == "rapid_fire":
                base_message += "\n\n💡 *Tu patrón de respuesta indica alta energía emocional.*"
            elif timing_pattern == "spaced":
                base_message += "\n\n💡 *Tus respuestas muestran un patrón meditativo y consciente.*"
        
        # Agregar recomendaciones según vulnerabilidad
        if vulnerability_assessment and vulnerability_assessment.get("success"):
            vulnerability_level = vulnerability_assessment.get("vulnerability_category", "moderate")
            if vulnerability_level == "high":
                base_message += "\n\n🤗 *Recomendación: Permite que las experiencias fluyan sin presión.*"
            elif vulnerability_level == "low":
                base_message += "\n\n✨ *Tu estabilidad emocional te permite explorar con confianza.*"
        
        return base_message

    async def _flujo_admin_shop_operation(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """
        Flujo para manejar operaciones administrativas de la tienda.

        Args:
            user_id: ID del usuario (debe ser administrador)
            **kwargs: Parámetros específicos de la operación (operation_type, item_data, etc.)

        Returns:
            Dict con resultados de la operación administrativa
        """
        try:
            operation_type = kwargs.get("operation_type")
            if not operation_type:
                return {
                    "success": False,
                    "message": "Tipo de operación no especificado."
                }

            # Import here to avoid circular imports
            from services.shop_admin_service import ShopAdminService

            admin_service = ShopAdminService(self.session)

            # Verificar permisos de administrador
            is_admin = await admin_service.verify_admin_permissions(user_id)
            if not is_admin:
                # Lucien maneja restricciones de acceso administrativo
                access_denied_message = self.character_voice.get_character_response(
                    CharacterType.LUCIEN,
                    EmotionalContext.PAUSA_REFLEXIVA,
                    "admin_access_denied"
                ) if self.character_voice else "Acceso denegado. Permisos de administrador requeridos."

                return {
                    "success": False,
                    "message": access_denied_message,
                    "action": "admin_access_denied"
                }

            # Procesar según el tipo de operación
            if operation_type == "create_item":
                return await self._handle_create_item_operation(admin_service, user_id, **kwargs)
            elif operation_type == "update_item":
                return await self._handle_update_item_operation(admin_service, user_id, **kwargs)
            elif operation_type == "delete_item":
                return await self._handle_delete_item_operation(admin_service, user_id, **kwargs)
            elif operation_type == "list_items":
                return await self._handle_list_items_operation(admin_service, user_id, **kwargs)
            elif operation_type == "view_analytics":
                return await self._handle_analytics_operation(admin_service, user_id, **kwargs)
            elif operation_type == "manage_inventory":
                return await self._handle_inventory_operation(admin_service, user_id, **kwargs)
            else:
                return {
                    "success": False,
                    "message": f"Operación '{operation_type}' no reconocida."
                }

        except Exception as e:
            logger.exception(f"Error en operación administrativa de tienda para usuario {user_id}: {str(e)}")
            return {
                "success": False,
                "message": "Error interno durante la operación administrativa.",
                "error": str(e)
            }

    async def _handle_create_item_operation(self, admin_service, user_id: int, **kwargs) -> Dict[str, Any]:
        """Maneja la creación de nuevos items en la tienda."""
        try:
            item_data = kwargs.get("item_data", {})
            result = await admin_service.create_shop_item(
                name=item_data.get("name"),
                description=item_data.get("description"),
                price=item_data.get("price"),
                is_vip_only=item_data.get("is_vip_only", False),
                category=item_data.get("category"),
                unlocks_lore_piece_id=item_data.get("unlocks_lore_piece_id")
            )

            if result["success"]:
                # Lucien confirma la creación exitosa como custodio del sistema
                success_message = self.character_voice.get_character_response(
                    CharacterType.LUCIEN,
                    EmotionalContext.PRESENTACION_CONTENIDO,
                    "admin_item_created",
                    {"item_name": item_data.get("name")}
                ) if self.character_voice else f"Artículo '{item_data.get('name')}' creado exitosamente."

                result["message"] = success_message

            return result

        except Exception as e:
            logger.exception(f"Error creando item: {str(e)}")
            return {
                "success": False,
                "message": "Error durante la creación del artículo.",
                "error": str(e)
            }

    async def _handle_update_item_operation(self, admin_service, user_id: int, **kwargs) -> Dict[str, Any]:
        """Maneja la actualización de items existentes."""
        try:
            item_id = kwargs.get("item_id")
            updates = kwargs.get("updates", {})

            if not item_id:
                return {
                    "success": False,
                    "message": "ID del artículo requerido para actualización."
                }

            result = await admin_service.update_shop_item(item_id, updates)

            if result["success"]:
                # Lucien confirma la actualización
                success_message = self.character_voice.get_character_response(
                    CharacterType.LUCIEN,
                    EmotionalContext.PRESENTACION_CONTENIDO,
                    "admin_item_updated",
                    {"item_id": item_id}
                ) if self.character_voice else f"Artículo {item_id} actualizado exitosamente."

                result["message"] = success_message

            return result

        except Exception as e:
            logger.exception(f"Error actualizando item: {str(e)}")
            return {
                "success": False,
                "message": "Error durante la actualización del artículo.",
                "error": str(e)
            }

    async def _handle_delete_item_operation(self, admin_service, user_id: int, **kwargs) -> Dict[str, Any]:
        """Maneja la eliminación de items de la tienda."""
        try:
            item_id = kwargs.get("item_id")

            if not item_id:
                return {
                    "success": False,
                    "message": "ID del artículo requerido para eliminación."
                }

            result = await admin_service.delete_shop_item(item_id)

            if result["success"]:
                # Lucien confirma la eliminación
                success_message = self.character_voice.get_character_response(
                    CharacterType.LUCIEN,
                    EmotionalContext.PAUSA_REFLEXIVA,
                    "admin_item_deleted",
                    {"item_id": item_id}
                ) if self.character_voice else f"Artículo {item_id} eliminado exitosamente."

                result["message"] = success_message

            return result

        except Exception as e:
            logger.exception(f"Error eliminando item: {str(e)}")
            return {
                "success": False,
                "message": "Error durante la eliminación del artículo.",
                "error": str(e)
            }

    async def _handle_list_items_operation(self, admin_service, user_id: int, **kwargs) -> Dict[str, Any]:
        """Maneja la listado administrativo de items."""
        try:
            filters = kwargs.get("filters", {})
            result = await admin_service.get_admin_shop_items(filters)

            if result["success"]:
                # Lucien presenta la información del inventario
                info_message = self.character_voice.get_character_response(
                    CharacterType.LUCIEN,
                    EmotionalContext.PRESENTACION_CONTENIDO,
                    "admin_inventory_overview",
                    {"item_count": len(result.get("items", []))}
                ) if self.character_voice else f"Mostrando {len(result.get('items', []))} artículos."

                result["message"] = info_message

            return result

        except Exception as e:
            logger.exception(f"Error listando items: {str(e)}")
            return {
                "success": False,
                "message": "Error al obtener el listado de artículos.",
                "error": str(e)
            }

    async def _handle_analytics_operation(self, admin_service, user_id: int, **kwargs) -> Dict[str, Any]:
        """Maneja la visualización de analytics de la tienda."""
        try:
            period = kwargs.get("period", "week")
            result = await admin_service.get_shop_analytics(period)

            if result["success"]:
                # Lucien presenta los datos analíticos
                analytics_message = self.character_voice.get_character_response(
                    CharacterType.LUCIEN,
                    EmotionalContext.PRESENTACION_CONTENIDO,
                    "admin_analytics_overview",
                    {"period": period, "analytics": result.get("analytics")}
                ) if self.character_voice else f"Analytics del período: {period}"

                result["message"] = analytics_message

            return result

        except Exception as e:
            logger.exception(f"Error obteniendo analytics: {str(e)}")
            return {
                "success": False,
                "message": "Error al obtener las estadísticas de la tienda.",
                "error": str(e)
            }

    async def _handle_inventory_operation(self, admin_service, user_id: int, **kwargs) -> Dict[str, Any]:
        """Maneja operaciones de gestión de inventario de usuarios."""
        try:
            target_user_id = kwargs.get("target_user_id")
            operation = kwargs.get("inventory_operation")

            if not target_user_id:
                return {
                    "success": False,
                    "message": "ID del usuario objetivo requerido."
                }

            if operation == "view":
                result = await admin_service.view_user_inventory(target_user_id)
            elif operation == "add_item":
                item_name = kwargs.get("item_name")
                result = await admin_service.add_item_to_user_inventory(target_user_id, item_name)
            elif operation == "remove_item":
                item_name = kwargs.get("item_name")
                result = await admin_service.remove_item_from_user_inventory(target_user_id, item_name)
            else:
                return {
                    "success": False,
                    "message": f"Operación de inventario '{operation}' no reconocida."
                }

            if result["success"]:
                # Lucien confirma la operación de inventario
                inventory_message = self.character_voice.get_character_response(
                    CharacterType.LUCIEN,
                    EmotionalContext.PRESENTACION_CONTENIDO,
                    f"admin_inventory_{operation}",
                    {"target_user_id": target_user_id, "operation": operation}
                ) if self.character_voice else f"Operación de inventario '{operation}' completada."

                result["message"] = inventory_message

            return result

        except Exception as e:
            logger.exception(f"Error en operación de inventario: {str(e)}")
            return {
                "success": False,
                "message": "Error durante la operación de inventario.",
                "error": str(e)
            }

    async def _flujo_admin_narrative_operation(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """
        Flujo para manejar operaciones administrativas de narrativa.

        Args:
            user_id: ID del usuario (debe ser administrador)
            **kwargs: Parámetros específicos de la operación (operation_type, fragment_data, etc.)

        Returns:
            Dict con resultados de la operación administrativa de narrativa
        """
        try:
            operation_type = kwargs.get("operation_type")
            if not operation_type:
                return {
                    "success": False,
                    "message": "Tipo de operación no especificado."
                }

            # Import here to avoid circular imports
            from services.narrative_admin_service import NarrativeAdminService

            narrative_admin_service = NarrativeAdminService(self.session)

            # Verificar permisos de administrador
            is_admin = await self._verify_admin_permissions(user_id)
            if not is_admin:
                # Lucien maneja restricciones de acceso administrativo
                access_denied_message = self.character_voice.get_character_response(
                    CharacterType.LUCIEN,
                    EmotionalContext.PAUSA_REFLEXIVA,
                    "admin_access_denied"
                ) if self.character_voice else "Acceso denegado. Permisos de administrador requeridos."

                return {
                    "success": False,
                    "message": access_denied_message,
                    "action": "admin_access_denied"
                }

            # Procesar según el tipo de operación
            if operation_type == "create_fragment":
                return await self._handle_create_fragment_operation(narrative_admin_service, user_id, **kwargs)
            elif operation_type == "update_fragment":
                return await self._handle_update_fragment_operation(narrative_admin_service, user_id, **kwargs)
            elif operation_type == "delete_fragment":
                return await self._handle_delete_fragment_operation(narrative_admin_service, user_id, **kwargs)
            elif operation_type == "validate_consistency":
                return await self._handle_validate_consistency_operation(narrative_admin_service, user_id, **kwargs)
            elif operation_type == "visualize_graph":
                return await self._handle_visualize_graph_operation(narrative_admin_service, user_id, **kwargs)
            elif operation_type == "bulk_import":
                return await self._handle_bulk_import_operation(narrative_admin_service, user_id, **kwargs)
            elif operation_type == "get_analytics":
                return await self._handle_narrative_analytics_operation(narrative_admin_service, user_id, **kwargs)
            else:
                return {
                    "success": False,
                    "message": f"Operación de narrativa '{operation_type}' no reconocida."
                }

        except Exception as e:
            logger.exception(f"Error en operación administrativa de narrativa para usuario {user_id}: {str(e)}")
            return {
                "success": False,
                "message": "Error interno durante la operación administrativa de narrativa.",
                "error": str(e)
            }

    async def _flujo_admin_lore_operation(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """
        Flujo para manejar operaciones administrativas de lore pieces.

        Args:
            user_id: ID del usuario (debe ser administrador)
            **kwargs: Parámetros específicos de la operación (operation_type, lore_data, etc.)

        Returns:
            Dict con resultados de la operación administrativa de lore
        """
        try:
            operation_type = kwargs.get("operation_type")
            if not operation_type:
                return {
                    "success": False,
                    "message": "Tipo de operación no especificado."
                }

            # Import here to avoid circular imports
            from services.lore_management_service import LoreManagementService

            lore_service = LoreManagementService(self.session)

            # Verificar permisos de administrador
            is_admin = await self._verify_admin_permissions(user_id)
            if not is_admin:
                # Lucien maneja restricciones de acceso administrativo
                access_denied_message = self.character_voice.get_character_response(
                    CharacterType.LUCIEN,
                    EmotionalContext.PAUSA_REFLEXIVA,
                    "admin_access_denied"
                ) if self.character_voice else "Acceso denegado. Permisos de administrador requeridos."

                return {
                    "success": False,
                    "message": access_denied_message,
                    "action": "admin_access_denied"
                }

            # Procesar según el tipo de operación
            if operation_type == "create_lore":
                return await self._handle_create_lore_operation(lore_service, user_id, **kwargs)
            elif operation_type == "update_lore":
                return await self._handle_update_lore_operation(lore_service, user_id, **kwargs)
            elif operation_type == "link_to_shop":
                return await self._handle_link_lore_to_shop_operation(lore_service, user_id, **kwargs)
            elif operation_type == "unlink_from_shop":
                return await self._handle_unlink_lore_from_shop_operation(lore_service, user_id, **kwargs)
            elif operation_type == "organize_by_category":
                return await self._handle_organize_lore_operation(lore_service, user_id, **kwargs)
            elif operation_type == "search_lore":
                return await self._handle_search_lore_operation(lore_service, user_id, **kwargs)
            elif operation_type == "get_unlock_analytics":
                return await self._handle_lore_unlock_analytics_operation(lore_service, user_id, **kwargs)
            elif operation_type == "bulk_lore_operations":
                return await self._handle_bulk_lore_operations(lore_service, user_id, **kwargs)
            else:
                return {
                    "success": False,
                    "message": f"Operación de lore '{operation_type}' no reconocida."
                }

        except Exception as e:
            logger.exception(f"Error en operación administrativa de lore para usuario {user_id}: {str(e)}")
            return {
                "success": False,
                "message": "Error interno durante la operación administrativa de lore.",
                "error": str(e)
            }

    async def _verify_admin_permissions(self, user_id: int) -> bool:
        """
        Verifica si el usuario tiene permisos de administrador.
        """
        try:
            # Import here to avoid circular imports
            from utils.user_roles import is_admin
            return await is_admin(user_id, self.session)
        except Exception as e:
            logger.error(f"Error verificando permisos de admin para usuario {user_id}: {str(e)}")
            return False

    # Narrative Admin Operation Handlers

    async def _handle_create_fragment_operation(self, narrative_admin_service, user_id: int, **kwargs) -> Dict[str, Any]:
        """Maneja la creación de fragmentos narrativos."""
        try:
            fragment_data = kwargs.get("fragment_data", {})
            result = await narrative_admin_service.create_story_fragment(fragment_data)

            if result.get("success", False):
                # Lucien confirma la creación exitosa como custodio del sistema
                success_message = self.character_voice.get_character_response(
                    CharacterType.LUCIEN,
                    EmotionalContext.PRESENTACION_CONTENIDO,
                    "admin_fragment_created",
                    {"fragment_key": fragment_data.get("key")}
                ) if self.character_voice else f"Fragmento '{fragment_data.get('key')}' creado exitosamente."

                result["message"] = success_message

            return result

        except Exception as e:
            logger.exception(f"Error creando fragmento narrativo: {str(e)}")
            return {
                "success": False,
                "message": "Error durante la creación del fragmento narrativo.",
                "error": str(e)
            }

    async def _handle_update_fragment_operation(self, narrative_admin_service, user_id: int, **kwargs) -> Dict[str, Any]:
        """Maneja la actualización de fragmentos narrativos."""
        try:
            fragment_id = kwargs.get("fragment_id")
            updates = kwargs.get("updates", {})

            if not fragment_id:
                return {
                    "success": False,
                    "message": "ID del fragmento requerido para actualización."
                }

            result = await narrative_admin_service.update_story_fragment(fragment_id, updates)

            if result.get("success", False):
                # Lucien confirma la actualización
                success_message = self.character_voice.get_character_response(
                    CharacterType.LUCIEN,
                    EmotionalContext.PRESENTACION_CONTENIDO,
                    "admin_fragment_updated",
                    {"fragment_id": fragment_id}
                ) if self.character_voice else f"Fragmento {fragment_id} actualizado exitosamente."

                result["message"] = success_message

            return result

        except Exception as e:
            logger.exception(f"Error actualizando fragmento narrativo: {str(e)}")
            return {
                "success": False,
                "message": "Error durante la actualización del fragmento narrativo.",
                "error": str(e)
            }

    async def _handle_delete_fragment_operation(self, narrative_admin_service, user_id: int, **kwargs) -> Dict[str, Any]:
        """Maneja la eliminación de fragmentos narrativos."""
        try:
            fragment_id = kwargs.get("fragment_id")

            if not fragment_id:
                return {
                    "success": False,
                    "message": "ID del fragmento requerido para eliminación."
                }

            result = await narrative_admin_service.delete_story_fragment(fragment_id)

            if result.get("success", False):
                # Lucien confirma la eliminación
                success_message = self.character_voice.get_character_response(
                    CharacterType.LUCIEN,
                    EmotionalContext.PAUSA_REFLEXIVA,
                    "admin_fragment_deleted",
                    {"fragment_id": fragment_id}
                ) if self.character_voice else f"Fragmento {fragment_id} eliminado exitosamente."

                result["message"] = success_message

            return result

        except Exception as e:
            logger.exception(f"Error eliminando fragmento narrativo: {str(e)}")
            return {
                "success": False,
                "message": "Error durante la eliminación del fragmento narrativo.",
                "error": str(e)
            }

    async def _handle_validate_consistency_operation(self, narrative_admin_service, user_id: int, **kwargs) -> Dict[str, Any]:
        """Maneja la validación de consistencia narrativa."""
        try:
            result = await narrative_admin_service.validate_narrative_consistency()

            if result.get("status") == "ok":
                # Lucien confirma que todo está en orden
                success_message = self.character_voice.get_character_response(
                    CharacterType.LUCIEN,
                    EmotionalContext.PRESENTACION_CONTENIDO,
                    "admin_consistency_ok"
                ) if self.character_voice else "La narrativa está consistente."

                result["message"] = success_message
                result["success"] = True
            elif result.get("status") == "issues_found":
                # Lucien reporta problemas encontrados
                issues_message = self.character_voice.get_character_response(
                    CharacterType.LUCIEN,
                    EmotionalContext.PAUSA_REFLEXIVA,
                    "admin_consistency_issues",
                    {"summary": result.get("summary")}
                ) if self.character_voice else "Se encontraron problemas de consistencia."

                result["message"] = issues_message
                result["success"] = True  # Successful validation, but with issues
            else:
                result["success"] = False
                result["message"] = "Error durante la validación de consistencia."

            return result

        except Exception as e:
            logger.exception(f"Error validando consistencia narrativa: {str(e)}")
            return {
                "success": False,
                "message": "Error durante la validación de consistencia narrativa.",
                "error": str(e)
            }

    async def _handle_visualize_graph_operation(self, narrative_admin_service, user_id: int, **kwargs) -> Dict[str, Any]:
        """Maneja la visualización del grafo narrativo."""
        try:
            result = await narrative_admin_service.visualize_narrative_graph()

            # Lucien presenta el grafo narrativo
            graph_message = self.character_voice.get_character_response(
                CharacterType.LUCIEN,
                EmotionalContext.PRESENTACION_CONTENIDO,
                "admin_graph_visualization"
            ) if self.character_voice else "Grafo narrativo generado."

            return {
                "success": True,
                "message": graph_message,
                "graph_data": result,
                "action": "graph_visualized"
            }

        except Exception as e:
            logger.exception(f"Error visualizando grafo narrativo: {str(e)}")
            return {
                "success": False,
                "message": "Error durante la visualización del grafo narrativo.",
                "error": str(e)
            }

    async def _handle_bulk_import_operation(self, narrative_admin_service, user_id: int, **kwargs) -> Dict[str, Any]:
        """Maneja la importación masiva de contenido narrativo."""
        try:
            file_data = kwargs.get("file_data")

            if not file_data:
                return {
                    "success": False,
                    "message": "Datos de archivo requeridos para importación masiva."
                }

            result = await narrative_admin_service.bulk_import_narrative_content(file_data)

            if result.get("success", False):
                # Lucien confirma la importación
                import_message = self.character_voice.get_character_response(
                    CharacterType.LUCIEN,
                    EmotionalContext.PRESENTACION_CONTENIDO,
                    "admin_bulk_import_success",
                    {"imported_count": result.get("imported_count", 0)}
                ) if self.character_voice else "Importación masiva completada."

                result["message"] = import_message

            return result

        except Exception as e:
            logger.exception(f"Error en importación masiva: {str(e)}")
            return {
                "success": False,
                "message": "Error durante la importación masiva de contenido narrativo.",
                "error": str(e)
            }

    async def _handle_narrative_analytics_operation(self, narrative_admin_service, user_id: int, **kwargs) -> Dict[str, Any]:
        """Maneja la obtención de analytics narrativos."""
        try:
            fragment_id = kwargs.get("fragment_id")
            result = await narrative_admin_service.get_fragment_with_analytics(fragment_id)

            # Lucien presenta los analytics
            analytics_message = self.character_voice.get_character_response(
                CharacterType.LUCIEN,
                EmotionalContext.PRESENTACION_CONTENIDO,
                "admin_narrative_analytics",
                {"fragment_id": fragment_id}
            ) if self.character_voice else f"Analytics del fragmento {fragment_id} obtenidos."

            return {
                "success": True,
                "message": analytics_message,
                "analytics_data": result,
                "action": "analytics_retrieved"
            }

        except Exception as e:
            logger.exception(f"Error obteniendo analytics narrativos: {str(e)}")
            return {
                "success": False,
                "message": "Error al obtener los analytics narrativos.",
                "error": str(e)
            }

    # Lore Admin Operation Handlers

    async def _handle_create_lore_operation(self, lore_service, user_id: int, **kwargs) -> Dict[str, Any]:
        """Maneja la creación de lore pieces."""
        try:
            lore_data = kwargs.get("lore_data", {})
            result = await lore_service.create_lore_piece(lore_data)

            if result.get("success", False):
                # Diana responde para contenido de lore (íntimo y personal)
                success_message = self.character_voice.get_character_response(
                    CharacterType.DIANA,
                    EmotionalContext.PRESENTACION_CONTENIDO,
                    "admin_lore_created",
                    {"lore_title": lore_data.get("title")}
                ) if self.character_voice else f"Lore '{lore_data.get('title')}' creado exitosamente."

                result["message"] = success_message

            return result

        except Exception as e:
            logger.exception(f"Error creando lore piece: {str(e)}")
            return {
                "success": False,
                "message": "Error durante la creación del lore piece.",
                "error": str(e)
            }

    async def _handle_update_lore_operation(self, lore_service, user_id: int, **kwargs) -> Dict[str, Any]:
        """Maneja la actualización de lore pieces."""
        try:
            lore_id = kwargs.get("lore_id")
            updates = kwargs.get("updates", {})

            if not lore_id:
                return {
                    "success": False,
                    "message": "ID del lore requerido para actualización."
                }

            result = await lore_service.update_lore_piece(lore_id, updates)

            if result.get("success", False):
                # Diana confirma la actualización
                success_message = self.character_voice.get_character_response(
                    CharacterType.DIANA,
                    EmotionalContext.PRESENTACION_CONTENIDO,
                    "admin_lore_updated",
                    {"lore_id": lore_id}
                ) if self.character_voice else f"Lore {lore_id} actualizado exitosamente."

                result["message"] = success_message

            return result

        except Exception as e:
            logger.exception(f"Error actualizando lore piece: {str(e)}")
            return {
                "success": False,
                "message": "Error durante la actualización del lore piece.",
                "error": str(e)
            }

    async def _handle_link_lore_to_shop_operation(self, lore_service, user_id: int, **kwargs) -> Dict[str, Any]:
        """Maneja la vinculación de lore pieces a items de tienda."""
        try:
            lore_id = kwargs.get("lore_id")
            shop_item_id = kwargs.get("shop_item_id")

            if not lore_id or not shop_item_id:
                return {
                    "success": False,
                    "message": "ID del lore e ID del item de tienda requeridos para vinculación."
                }

            result = await lore_service.link_lore_to_shop_item(lore_id, shop_item_id)

            if result.get("success", False):
                # Diana confirma la vinculación (contenido íntimo con compras)
                link_message = self.character_voice.get_character_response(
                    CharacterType.DIANA,
                    EmotionalContext.INTIMIDAD_PROFUNDA,
                    "admin_lore_linked",
                    {"lore_id": lore_id, "shop_item_id": shop_item_id}
                ) if self.character_voice else f"Lore {lore_id} vinculado al item {shop_item_id}."

                result["message"] = link_message

            return result

        except Exception as e:
            logger.exception(f"Error vinculando lore a item de tienda: {str(e)}")
            return {
                "success": False,
                "message": "Error durante la vinculación de lore al item de tienda.",
                "error": str(e)
            }

    async def _handle_unlink_lore_from_shop_operation(self, lore_service, user_id: int, **kwargs) -> Dict[str, Any]:
        """Maneja la desvinculación de lore pieces de items de tienda."""
        try:
            lore_id = kwargs.get("lore_id")
            shop_item_id = kwargs.get("shop_item_id")

            if not lore_id or not shop_item_id:
                return {
                    "success": False,
                    "message": "ID del lore e ID del item de tienda requeridos para desvinculación."
                }

            result = await lore_service.unlink_lore_from_shop_item(lore_id, shop_item_id)

            if result.get("success", False):
                # Lucien maneja la desvinculación (acción técnica)
                unlink_message = self.character_voice.get_character_response(
                    CharacterType.LUCIEN,
                    EmotionalContext.PRESENTACION_CONTENIDO,
                    "admin_lore_unlinked",
                    {"lore_id": lore_id, "shop_item_id": shop_item_id}
                ) if self.character_voice else f"Lore {lore_id} desvinculado del item {shop_item_id}."

                result["message"] = unlink_message

            return result

        except Exception as e:
            logger.exception(f"Error desvinculando lore de item de tienda: {str(e)}")
            return {
                "success": False,
                "message": "Error durante la desvinculación de lore del item de tienda.",
                "error": str(e)
            }

    async def _handle_organize_lore_operation(self, lore_service, user_id: int, **kwargs) -> Dict[str, Any]:
        """Maneja la organización de lore pieces por categoría."""
        try:
            category_filters = kwargs.get("category_filters", {})
            result = await lore_service.organize_lore_by_category(category_filters)

            # Diana presenta la organización de contenido
            organize_message = self.character_voice.get_character_response(
                CharacterType.DIANA,
                EmotionalContext.PRESENTACION_CONTENIDO,
                "admin_lore_organized"
            ) if self.character_voice else "Lore organizado por categorías."

            return {
                "success": True,
                "message": organize_message,
                "categorized_lore": result,
                "action": "lore_organized"
            }

        except Exception as e:
            logger.exception(f"Error organizando lore por categoría: {str(e)}")
            return {
                "success": False,
                "message": "Error durante la organización de lore por categoría.",
                "error": str(e)
            }

    async def _handle_search_lore_operation(self, lore_service, user_id: int, **kwargs) -> Dict[str, Any]:
        """Maneja la búsqueda de lore pieces."""
        try:
            search_criteria = kwargs.get("search_criteria", {})
            results = await lore_service.search_lore_pieces(search_criteria)

            # Lucien presenta los resultados de búsqueda
            search_message = self.character_voice.get_character_response(
                CharacterType.LUCIEN,
                EmotionalContext.PRESENTACION_CONTENIDO,
                "admin_lore_search_results",
                {"results_count": len(results)}
            ) if self.character_voice else f"Búsqueda completada: {len(results)} resultados."

            return {
                "success": True,
                "message": search_message,
                "search_results": results,
                "action": "lore_search_completed"
            }

        except Exception as e:
            logger.exception(f"Error en búsqueda de lore: {str(e)}")
            return {
                "success": False,
                "message": "Error durante la búsqueda de lore pieces.",
                "error": str(e)
            }

    async def _handle_lore_unlock_analytics_operation(self, lore_service, user_id: int, **kwargs) -> Dict[str, Any]:
        """Maneja la obtención de analytics de desbloqueos de lore."""
        try:
            lore_id = kwargs.get("lore_id")

            if not lore_id:
                return {
                    "success": False,
                    "message": "ID del lore requerido para analytics de desbloqueos."
                }

            analytics = await lore_service.get_lore_unlock_analytics(lore_id)

            # Lucien presenta los analytics de desbloqueos
            analytics_message = self.character_voice.get_character_response(
                CharacterType.LUCIEN,
                EmotionalContext.PRESENTACION_CONTENIDO,
                "admin_lore_unlock_analytics",
                {"lore_id": lore_id, "analytics": analytics}
            ) if self.character_voice else f"Analytics de desbloqueos para lore {lore_id} obtenidos."

            return {
                "success": True,
                "message": analytics_message,
                "unlock_analytics": analytics,
                "action": "unlock_analytics_retrieved"
            }

        except Exception as e:
            logger.exception(f"Error obteniendo analytics de desbloqueos: {str(e)}")
            return {
                "success": False,
                "message": "Error al obtener los analytics de desbloqueos.",
                "error": str(e)
            }

    async def _handle_bulk_lore_operations(self, lore_service, user_id: int, **kwargs) -> Dict[str, Any]:
        """Maneja operaciones masivas de lore pieces."""
        try:
            bulk_operation = kwargs.get("bulk_operation")
            operation_data = kwargs.get("operation_data", {})

            if not bulk_operation:
                return {
                    "success": False,
                    "message": "Tipo de operación masiva no especificado."
                }

            # Coordinar diferentes tipos de operaciones masivas
            if bulk_operation == "bulk_category_update":
                # Actualizar categorías en lote
                category_updates = operation_data.get("category_updates", {})
                results = []
                for lore_id, new_category in category_updates.items():
                    result = await lore_service.update_lore_piece(lore_id, {"category": new_category})
                    results.append({"lore_id": lore_id, "result": result})

                success_count = sum(1 for r in results if r["result"].get("success"))

                # Diana confirma las operaciones masivas
                bulk_message = self.character_voice.get_character_response(
                    CharacterType.DIANA,
                    EmotionalContext.PRESENTACION_CONTENIDO,
                    "admin_bulk_lore_update",
                    {"success_count": success_count, "total_count": len(results)}
                ) if self.character_voice else f"Operación masiva completada: {success_count}/{len(results)} exitosas."

                return {
                    "success": True,
                    "message": bulk_message,
                    "bulk_results": results,
                    "action": "bulk_operation_completed"
                }

            elif bulk_operation == "bulk_status_update":
                # Activar/desactivar lore pieces en lote
                status_updates = operation_data.get("status_updates", {})
                results = []
                for lore_id, is_active in status_updates.items():
                    result = await lore_service.update_lore_piece(lore_id, {"is_active": is_active})
                    results.append({"lore_id": lore_id, "result": result})

                success_count = sum(1 for r in results if r["result"].get("success"))

                # Lucien maneja cambios de estado masivos
                bulk_message = self.character_voice.get_character_response(
                    CharacterType.LUCIEN,
                    EmotionalContext.PRESENTACION_CONTENIDO,
                    "admin_bulk_status_update",
                    {"success_count": success_count, "total_count": len(results)}
                ) if self.character_voice else f"Actualización de estado masiva: {success_count}/{len(results)} exitosas."

                return {
                    "success": True,
                    "message": bulk_message,
                    "bulk_results": results,
                    "action": "bulk_status_update_completed"
                }

            else:
                return {
                    "success": False,
                    "message": f"Operación masiva '{bulk_operation}' no reconocida."
                }

        except Exception as e:
            logger.exception(f"Error en operaciones masivas de lore: {str(e)}")
            return {
                "success": False,
                "message": "Error durante las operaciones masivas de lore.",
                "error": str(e)
            }
