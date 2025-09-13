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
        
        # 5. Decisión exitosa con voz auténtica
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
            
            # If purchase was successful, add to backpack
            if result.get("success") and result.get("unlocked_lore"):
                # Add the item to the user's backpack
                await self.ejecutar_flujo(
                    user_id,
                    AccionUsuario.AGREGAR_A_MOCHILA,
                    item_id=item_id,
                    **kwargs
                )
            
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

    async def _flujo_agregar_a_mochila(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """
        Flujo para agregar items comprados a la mochila del usuario.
        """
        try:
            item_id = kwargs.get("item_id")
            if not item_id:
                return {
                    "success": False,
                    "message": "ID de artículo no proporcionado."
                }
            
            # Import here to avoid circular imports
            from database.models import UserLorePiece, LorePiece, ShopItem
            from datetime import datetime
            from sqlalchemy import select
            
            # Get the shop item to find the associated lore piece
            stmt = select(ShopItem).where(ShopItem.id == item_id)
            result = await self.session.execute(stmt)
            shop_item = result.scalar_one_or_none()
            
            if not shop_item:
                return {
                    "success": False,
                    "message": "Artículo no encontrado."
                }
            
            # Check if the item unlocks a lore piece
            if shop_item.unlocks_lore_piece_id:
                # Check if the user already has this lore piece
                stmt = select(UserLorePiece).where(
                    UserLorePiece.user_id == user_id,
                    UserLorePiece.lore_piece_id == shop_item.unlocks_lore_piece_id
                )
                result = await self.session.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if not existing:
                    # Add to user's lore pieces (backpack)
                    user_lore_piece = UserLorePiece(
                        user_id=user_id,
                        lore_piece_id=shop_item.unlocks_lore_piece_id,
                        context={
                            'source': 'shop_purchase',
                            'item_id': item_id,
                            'item_name': shop_item.name,
                            'purchased_at': datetime.utcnow().isoformat()
                        }
                    )
                    self.session.add(user_lore_piece)
                    await self.session.flush()
                    
                    # Get the lore piece details
                    lore_piece = await self.session.get(LorePiece, shop_item.unlocks_lore_piece_id)
                    
                    return {
                        "success": True,
                        "message": f"¡{lore_piece.title} ha sido agregado a tu mochila!",
                        "lore_piece": lore_piece.title
                    }
                else:
                    return {
                        "success": False,
                        "message": "Ya tienes este ítem en tu mochila."
                    }
            else:
                return {
                    "success": False,
                    "message": "Este ítem no desbloquea contenido para la mochila."
                }
        except Exception as e:
            logger.exception(f"Error agregando a mochila para usuario {user_id}: {str(e)}")
            return {
                "success": False,
                "message": "Error al agregar el ítem a la mochila.",
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
