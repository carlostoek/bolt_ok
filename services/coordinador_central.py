import enum
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    from .integration.channel_engagement_service import ChannelEngagementService
    from .integration.narrative_point_service import NarrativePointService
    from .integration.narrative_access_service import NarrativeAccessService
    from .integration.shop_integration_service import ShopIntegrationService
    from .narrative_service import NarrativeService
    from .point_service import PointService
    from .emotional_analysis_service import EmotionalAnalysisService
    from .character_voice_service import CharacterVoiceService, CharacterType, EmotionalContext
except ImportError:
    # Fallback to absolute imports for standalone usage
    from services.integration.channel_engagement_service import ChannelEngagementService
    from services.integration.narrative_point_service import NarrativePointService
    from services.integration.narrative_access_service import NarrativeAccessService
    from services.integration.shop_integration_service import ShopIntegrationService
    from services.narrative_service import NarrativeService
    from services.point_service import PointService
    from services.emotional_analysis_service import EmotionalAnalysisService
    from services.character_voice_service import CharacterVoiceService, CharacterType, EmotionalContext

class AccionUsuario(enum.Enum):
    """Enumeración de acciones de usuario que pueden desencadenar flujos integrados."""
    REACCIONAR_PUBLICACION = "reaccionar_publicacion"
    ACCEDER_NARRATIVA_VIP = "acceder_narrativa_vip"
    TOMAR_DECISION = "tomar_decision"
    PARTICIPAR_CANAL = "participar_canal"
    VERIFICAR_ENGAGEMENT = "verificar_engagement"
    TEST_EVALUACION_EMOCIONAL = "test_evaluacion_emocional"
    COMPRAR_ARTICULO = "comprar_articulo"
    LISTAR_TIENDA = "listar_tienda"
    VER_INVENTARIO = "ver_inventario"

class CoordinadorCentral:
    """
    Coordinador central que orquesta todos los servicios integrados.
    Maneja flujos complejos que requieren múltiples servicios trabajando en conjunto.
    """
    
    def __init__(self, session):
        self.session = session
        
        # Servicios de integración
        self.channel_engagement = ChannelEngagementService(session)
        self.narrative_point = NarrativePointService(session)
        self.narrative_access = NarrativeAccessService(session)
        self.shop_integration = ShopIntegrationService(session)
        # Servicios base
        self.narrative_service = NarrativeService(session)
        self.point_service = PointService(session)
        
        # Servicios opcionales (pueden no estar disponibles)
        self.emotional_analysis = None
        self.character_voice = None
        
        try:
            self.emotional_analysis = EmotionalAnalysisService(session)
            self.character_voice = CharacterVoiceService(session)
        except Exception as e:
            logger.warning(f"Servicios opcionales no disponibles: {str(e)}")
    
    async def ejecutar_flujo(self, accion: AccionUsuario, user_id: int, **kwargs) -> Dict[str, Any]:
        """
        Ejecuta el flujo correspondiente a la acción especificada.
        
        Args:
            accion: Tipo de acción a ejecutar
            user_id: ID del usuario que ejecuta la acción
            **kwargs: Parámetros adicionales específicos de cada flujo
            
        Returns:
            Dict con resultado del flujo ejecutado
        """
        try:
            if accion == AccionUsuario.REACCIONAR_PUBLICACION:
                return await self._flujo_reaccionar_publicacion(user_id, **kwargs)
            elif accion == AccionUsuario.ACCEDER_NARRATIVA_VIP:
                return await self._flujo_acceder_narrativa_vip(user_id, **kwargs)
            elif accion == AccionUsuario.TOMAR_DECISION:
                return await self._flujo_tomar_decision(user_id, **kwargs)
            elif accion == AccionUsuario.PARTICIPAR_CANAL:
                return await self._flujo_participar_canal(user_id, **kwargs)
            elif accion == AccionUsuario.VERIFICAR_ENGAGEMENT:
                return await self._flujo_verificar_engagement(user_id, **kwargs)
            elif accion == AccionUsuario.TEST_EVALUACION_EMOCIONAL:
                return await self._flujo_test_evaluacion_emocional(user_id, **kwargs)
            elif accion == AccionUsuario.COMPRAR_ARTICULO:
                return await self._flujo_comprar_articulo(user_id, **kwargs)
            elif accion == AccionUsuario.LISTAR_TIENDA:
                return await self._flujo_listar_tienda(user_id, **kwargs)
            elif accion == AccionUsuario.VER_INVENTARIO:
                return await self._flujo_ver_inventario(user_id, **kwargs)
            else:
                logger.warning(f"Acción no implementada: {accion}")
                return {
                    "success": False,
                    "message": f"Acción {accion.value} no implementada",
                    "action": "not_implemented"
                }
                
        except Exception as e:
            logger.exception(f"Error ejecutando flujo {accion.value} para usuario {user_id}: {str(e)}")
            return {
                "success": False,
                "message": "Error interno del sistema",
                "action": "system_error",
                "error": str(e)
            }
    
    async def _flujo_reaccionar_publicacion(self, user_id: int, post_id: int, reaction_type: str, bot=None) -> Dict[str, Any]:
        """
        Flujo completo para procesar reacción a publicación.
        Integra engagement, puntos narrativos y análisis emocional.
        """
        try:
            # 1. Procesar engagement del canal
            engagement_result = await self.channel_engagement.process_post_reaction(
                user_id, post_id, reaction_type, bot
            )
            
            if not engagement_result["success"]:
                return engagement_result
            
            # 2. Procesar puntos narrativos si hay engagement
            narrative_result = await self.narrative_point.process_narrative_interaction(
                user_id, "post_reaction", {"post_id": post_id, "reaction": reaction_type}
            )
            
            # 3. Análisis emocional opcional
            emotional_context = None
            if self.emotional_analysis:
                try:
                    emotional_context = await self.emotional_analysis.analyze_reaction_pattern(
                        user_id, reaction_type, post_id
                    )
                except Exception as e:
                    logger.debug(f"Análisis emocional falló para usuario {user_id}: {str(e)}")
            
            # 4. Combinar resultados
            combined_message = engagement_result["message"]
            if narrative_result["success"] and narrative_result.get("narrative_unlocked"):
                combined_message += f"\n\n{narrative_result['message']}"
            
            return {
                "success": True,
                "message": combined_message,
                "action": "reaction_processed",
                "engagement_data": engagement_result,
                "narrative_data": narrative_result,
                "emotional_context": emotional_context
            }
            
        except Exception as e:
            logger.exception(f"Error en flujo de reacción para usuario {user_id}: {str(e)}")
            return {
                "success": False,
                "message": "Error procesando reacción",
                "action": "reaction_error",
                "error": str(e)
            }
    
    async def _flujo_acceder_narrativa_vip(self, user_id: int, narrative_id: int, bot=None) -> Dict[str, Any]:
        """
        Flujo para acceso a narrativa VIP.
        Integra verificación de acceso, puntos y personalización emocional.
        """
        try:
            # 1. Verificar acceso VIP
            access_result = await self.narrative_access.verify_vip_narrative_access(
                user_id, narrative_id, bot
            )
            
            if not access_result["success"]:
                return access_result
            
            # 2. Procesar puntos por acceso VIP
            narrative_result = await self.narrative_point.process_narrative_interaction(
                user_id, "vip_access", {"narrative_id": narrative_id}
            )
            
            # 3. Personalización con voz de personaje
            base_message = access_result["message"]
            if self.character_voice and access_result.get("narrative_content"):
                try:
                    # Determinar contexto emocional
                    user_points = await self.point_service.get_user_points(user_id)
                    user_history = {"total_interactions": user_points // 10}
                    
                    emotional_context_enum = EmotionalContext.USUARIO_AVANZADO if user_points > 50 else EmotionalContext.NUEVO_USUARIO
                    
                    personalized_message = self.character_voice.get_character_response(
                        CharacterType.DIANA,  # Diana maneja contenido VIP
                        emotional_context_enum,
                        "vip_narrative_access",
                        None,
                        user_history
                    )
                    
                    base_message = f"{personalized_message}\n\n{base_message}"
                    
                except Exception as e:
                    logger.debug(f"Personalización de voz falló: {str(e)}")
            
            return {
                "success": True,
                "message": base_message,
                "action": "vip_access_granted",
                "access_data": access_result,
                "narrative_data": narrative_result
            }
            
        except Exception as e:
            logger.exception(f"Error en flujo VIP para usuario {user_id}: {str(e)}")
            return {
                "success": False,
                "message": "Error accediendo a contenido VIP",
                "action": "vip_access_error",
                "error": str(e)
            }
    
    async def _flujo_tomar_decision(self, user_id: int, decision_id: int, choice: str, bot=None) -> Dict[str, Any]:
        """
        Flujo para toma de decisiones narrativas.
        Integra puntos, análisis emocional y consecuencias narrativas.
        """
        try:
            # 1. Procesar decisión narrativa
            narrative_result = await self.narrative_point.process_narrative_interaction(
                user_id, "decision_made", {"decision_id": decision_id, "choice": choice}
            )
            
            # 2. Análisis emocional de la decisión
            emotional_context = None
            if self.emotional_analysis:
                try:
                    emotional_context = await self.emotional_analysis.analyze_decision_pattern(
                        user_id, decision_id, choice
                    )
                except Exception as e:
                    logger.debug(f"Análisis emocional de decisión falló: {str(e)}")
            
            # 3. Personalización con voz de personaje
            base_message = narrative_result["message"]
            if self.character_voice:
                try:
                    user_points = await self.point_service.get_user_points(user_id)
                    user_history = {"total_interactions": user_points // 5}
                    
                    # Mapear análisis emocional a contexto
                    emotional_context_enum = self.character_voice.map_emotional_analysis_to_context(
                        emotional_context, emotional_context, None, user_history
                    ) if emotional_context else EmotionalContext.ENGAGEMENT_MEDIO
                    
                    # Lucien maneja decisiones importantes
                    personalized_response = self.character_voice.get_character_response(
                        CharacterType.LUCIEN,
                        emotional_context_enum,
                        "decision_consequence",
                        emotional_context,
                        user_history
                    )
                    
                    base_message = f"{personalized_response}\n\n{base_message}"
                    
                except Exception as e:
                    logger.debug(f"Personalización de decisión falló: {str(e)}")
            
            return {
                "success": True,
                "message": base_message,
                "action": "decision_processed",
                "narrative_data": narrative_result,
                "emotional_context": emotional_context
            }
            
        except Exception as e:
            logger.exception(f"Error en flujo de decisión para usuario {user_id}: {str(e)}")
            return {
                "success": False,
                "message": "Error procesando decisión",
                "action": "decision_error",
                "error": str(e)
            }
    
    async def _flujo_participar_canal(self, user_id: int, channel_id: int, participation_type: str, bot=None) -> Dict[str, Any]:
        """
        Flujo para participación en canal.
        Integra engagement y recompensas narrativas.
        """
        try:
            # 1. Procesar participación en canal
            engagement_result = await self.channel_engagement.process_channel_participation(
                user_id, channel_id, participation_type, bot
            )
            
            if not engagement_result["success"]:
                return engagement_result
            
            # 2. Procesar puntos por participación
            narrative_result = await self.narrative_point.process_narrative_interaction(
                user_id, "channel_participation", {
                    "channel_id": channel_id, 
                    "type": participation_type
                }
            )
            
            # 3. Combinar mensajes
            combined_message = engagement_result["message"]
            if narrative_result["success"] and narrative_result.get("points_awarded", 0) > 0:
                combined_message += f"\n\n{narrative_result['message']}"
            
            return {
                "success": True,
                "message": combined_message,
                "action": "participation_processed",
                "engagement_data": engagement_result,
                "narrative_data": narrative_result
            }
            
        except Exception as e:
            logger.exception(f"Error en flujo de participación para usuario {user_id}: {str(e)}")
            return {
                "success": False,
                "message": "Error procesando participación",
                "action": "participation_error",
                "error": str(e)
            }
    
    async def _flujo_verificar_engagement(self, user_id: int, bot=None) -> Dict[str, Any]:
        """
        Flujo para verificar estado de engagement del usuario.
        Proporciona resumen completo de actividad.
        """
        try:
            # 1. Obtener métricas de engagement
            engagement_metrics = await self.channel_engagement.get_user_engagement_summary(user_id)
            
            # 2. Obtener progreso narrativo
            narrative_progress = await self.narrative_point.get_user_narrative_progress(user_id)
            
            # 3. Combinar información
            summary_message = "📊 **Resumen de tu actividad:**\n\n"
            
            if engagement_metrics["success"]:
                metrics = engagement_metrics["metrics"]
                summary_message += f"💬 Interacciones: {metrics.get('total_interactions', 0)}\n"
                summary_message += f"❤️ Reacciones: {metrics.get('total_reactions', 0)}\n"
                summary_message += f"📅 Días activo: {metrics.get('active_days', 0)}\n\n"
            
            if narrative_progress["success"]:
                progress = narrative_progress["progress"]
                summary_message += f"⭐ Puntos narrativos: {progress.get('total_points', 0)}\n"
                summary_message += f"🔓 Contenido desbloqueado: {progress.get('unlocked_content', 0)}\n"
                summary_message += f"🎯 Nivel actual: {progress.get('current_level', 1)}\n"
            
            return {
                "success": True,
                "message": summary_message,
                "action": "engagement_verified",
                "engagement_metrics": engagement_metrics,
                "narrative_progress": narrative_progress
            }
            
        except Exception as e:
            logger.exception(f"Error verificando engagement para usuario {user_id}: {str(e)}")
            return {
                "success": False,
                "message": "Error obteniendo resumen de actividad",
                "action": "verification_error",
                "error": str(e)
            }
    
    async def _flujo_test_evaluacion_emocional(self, user_id: int, test_responses: Dict[str, Any], bot=None) -> Dict[str, Any]:
        """
        Flujo para procesar test de evaluación emocional.
        Integra análisis emocional con recompensas narrativas.
        """
        try:
            # 1. Procesar análisis emocional si está disponible
            emotional_result = None
            if self.emotional_analysis:
                try:
                    emotional_result = await self.emotional_analysis.process_emotional_assessment(
                        user_id, test_responses
                    )
                except Exception as e:
                    logger.debug(f"Análisis emocional falló: {str(e)}")
                    emotional_result = {
                        "success": False,
                        "message": "Análisis emocional no disponible"
                    }
            
            # 2. Procesar puntos por completar evaluación
            narrative_result = await self.narrative_point.process_narrative_interaction(
                user_id, "emotional_assessment", {"responses": test_responses}
            )
            
            # 3. Generar respuesta personalizada
            base_message = "🧠 **Evaluación emocional completada**\n\n"
            
            if emotional_result and emotional_result.get("success"):
                base_message += f"{emotional_result['message']}\n\n"
            
            if narrative_result["success"]:
                base_message += f"{narrative_result['message']}"
            
            # 4. Personalización con voz de personaje
            if self.character_voice and emotional_result:
                try:
                    user_points = await self.point_service.get_user_points(user_id)
                    user_history = {"total_interactions": user_points // 8}
                    
                    # Diana maneja evaluaciones emocionales (introspección)
                    personalized_response = self.character_voice.get_character_response(
                        CharacterType.DIANA,
                        EmotionalContext.PAUSA_REFLEXIVA,
                        "emotional_assessment_complete",
                        emotional_result.get("emotional_context"),
                        user_history
                    )
                    
                    base_message = f"{personalized_response}\n\n{base_message}"
                    
                except Exception as e:
                    logger.debug(f"Personalización de evaluación falló: {str(e)}")
        
        return base_message
    
    async def _flujo_comprar_articulo(self, user_id: int, item_id: int, bot=None) -> Dict[str, Any]:
        """
        Flujo para procesar compra de artículo en tienda.
        Integra verificación de puntos, acceso VIP y desbloqueo de pistas.
        """
        try:
            # 1. Análisis emocional de la compra (opcional)
            emotional_context = None
            if self.emotional_analysis:
                try:
                    import datetime
                    emotional_context = await self.emotional_analysis.analyze_response_timing(
                        user_id, datetime.datetime.utcnow(), "shop_purchase"
                    )
                except Exception as e:
                    logger.debug(f"Análisis emocional de compra falló para usuario {user_id}: {str(e)}")
            
            # 2. Procesar compra a través del servicio de integración
            purchase_result = await self.shop_integration.process_item_purchase(
                user_id, item_id, bot
            )
            
            if not purchase_result["success"]:
                # Compra fallida - Lucien maneja errores como custodio
                error_message = self.character_voice.get_character_response(
                    CharacterType.LUCIEN,
                    EmotionalContext.PAUSA_REFLEXIVA,
                    "purchase_failed",
                    emotional_context
                ) if self.character_voice else purchase_result["message"]
                
                return {
                    "success": False,
                    "message": f"{error_message}\n\n*{purchase_result['message']}*",
                    "action": purchase_result["action"],
                    "emotional_context": emotional_context
                }
            
            # 3. Compra exitosa - Diana celebra la adquisición
            user_points = await self.point_service.get_user_points(user_id)
            user_history = {"total_interactions": user_points // 10}
            
            emotional_context_enum = self.character_voice.map_emotional_analysis_to_context(
                emotional_context, emotional_context, None, user_history
            ) if self.character_voice else EmotionalContext.ENGAGEMENT_ALTO
            
            # Diana responde a compras exitosas (momentos de inversión)
            success_message = self.character_voice.get_character_response(
                CharacterType.DIANA,
                emotional_context_enum,
                "purchase_success",
                emotional_context,
                user_history
            ) if self.character_voice else purchase_result["message"]
            
            # Agregar información de la compra
            purchase_data = purchase_result.get("purchase_data", {})
            if purchase_data.get("lore_unlocked"):
                success_message += f"\n\n*🗝️ Has desbloqueado: {purchase_data['lore_unlocked']}*"
            
            return {
                "success": True,
                "message": success_message,
                "action": "purchase_completed",
                "purchase_data": purchase_data,
                "side_effects": purchase_result.get("side_effects", {}),
                "emotional_context": emotional_context
            }
            
        except Exception as e:
            logger.exception(f"Error en flujo de compra para usuario {user_id}: {str(e)}")
            return {
                "success": False,
                "message": "Error inesperado durante la compra. Intenta nuevamente.",
                "action": "purchase_error",
                "error": str(e)
            }
    
    async def _flujo_listar_tienda(self, user_id: int, category: str = None, bot=None) -> Dict[str, Any]:
        """
        Flujo para mostrar catálogo de tienda personalizado.
        Integra verificación VIP y recomendaciones personalizadas.
        """
        try:
            # 1. Obtener catálogo personalizado
            catalog_result = await self.shop_integration.get_personalized_shop_catalog(user_id)
            
            if not catalog_result["success"]:
                # Error obteniendo catálogo - Lucien maneja errores
                error_message = self.character_voice.get_character_response(
                    CharacterType.LUCIEN,
                    EmotionalContext.PAUSA_REFLEXIVA,
                    "access_denied"
                ) if self.character_voice else catalog_result["message"]
                
                return {
                    "success": False,
                    "message": error_message,
                    "action": "catalog_error"
                }
            
            # 2. Generar mensaje de bienvenida a la tienda
            user_points = catalog_result["user_points"]
            is_vip = catalog_result["is_vip"]
            total_items = catalog_result["total_items"]
            
            # Determinar contexto emocional para mensaje de tienda
            user_history = {"total_interactions": user_points // 5}
            emotional_context_enum = EmotionalContext.USUARIO_AVANZADO if user_points > 100 else EmotionalContext.NUEVO_USUARIO
            
            # Diana presenta la tienda como extensión de su mundo
            if is_vip:
                welcome_message = self.character_voice.get_character_response(
                    CharacterType.DIANA,
                    EmotionalContext.USUARIO_AVANZADO,
                    "shop_vip_welcome",
                    None,
                    user_history
                ) if self.character_voice else "Bienvenido a mi tienda exclusiva"
            else:
                welcome_message = self.character_voice.get_character_response(
                    CharacterType.DIANA,
                    emotional_context_enum,
                    "shop_welcome",
                    None,
                    user_history
                ) if self.character_voice else "Bienvenido a mi tienda"
            
            # Crear mensaje completo de tienda
            shop_message = f"{welcome_message}\n\n"
            shop_message += f"🛒 **Mi Tienda Personal**\n\n"
            shop_message += f"💰 **Tus besitos**: {user_points}\n"
            shop_message += f"📦 **Artículos disponibles**: {total_items}\n"
            
            if is_vip:
                shop_message += f"💎 **Acceso VIP**: Todos los artículos disponibles\n"
            else:
                vip_items = sum(
                    len([item for item in items if item.get("is_vip_exclusive")])
                    for items in catalog_result["items_by_category"].values()
                )
                if vip_items > 0:
                    shop_message += f"🔒 **Artículos VIP**: {vip_items} (requiere suscripción)\n"
            
            shop_message += f"\n*Cada artículo ha sido elegido cuidadosamente para enriquecer tu experiencia...*"
            
            return {
                "success": True,
                "message": shop_message,
                "action": "catalog_displayed",
                "catalog_data": catalog_result
            }
            
        except Exception as e:
            logger.exception(f"Error en flujo de listado de tienda para usuario {user_id}: {str(e)}")
            return {
                "success": False,
                "message": "Error cargando la tienda. Intenta nuevamente.",
                "action": "catalog_error",
                "error": str(e)
            }
    
    async def _flujo_ver_inventario(self, user_id: int, bot=None) -> Dict[str, Any]:
        """
        Flujo para mostrar inventario del usuario.
        Integra con sistema de pistas narrativas.
        """
        try:
            # 1. Obtener resumen del inventario
            inventory_summary = await self.shop_integration.get_user_shop_summary(user_id)
            
            if not inventory_summary["success"]:
                return {
                    "success": False,
                    "message": inventory_summary["message"],
                    "action": "inventory_error"
                }
            
            # 2. Generar mensaje de inventario con voz auténtica
            inventory_count = inventory_summary["inventory_count"]
            total_spent = inventory_summary["total_spent"]
            
            # Lucien presenta el inventario como custodio de posesiones
            inventory_message = self.character_voice.get_character_response(
                CharacterType.LUCIEN,
                EmotionalContext.USUARIO_AVANZADO if inventory_count > 5 else EmotionalContext.NUEVO_USUARIO,
                "inventory_presentation"
            ) if self.character_voice else "Tu inventario personal"
            
            inventory_text = f"{inventory_message}\n\n"
            inventory_text += f"📦 **Tu Colección Personal**\n\n"
            inventory_text += f"🎒 **Artículos**: {inventory_count}\n"
            inventory_text += f"💸 **Total invertido**: {total_spent} besitos\n"
            
            if inventory_summary.get("recent_purchases"):
                inventory_text += f"\n🛍️ **Compras recientes**:\n"
                for purchase in inventory_summary["recent_purchases"][:3]:
                    inventory_text += f"• {purchase['item_name']} ({purchase['price_paid']}💋)\n"
            
            return {
                "success": True,
                "message": inventory_text,
                "action": "inventory_displayed",
                "inventory_data": inventory_summary
            }
            
        except Exception as e:
            logger.exception(f"Error en flujo de inventario para usuario {user_id}: {str(e)}")
            return {
                "success": False,
                "message": "Error cargando tu inventario.",
                "action": "inventory_error",
                "error": str(e)
            }