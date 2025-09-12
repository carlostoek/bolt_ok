@@ .. @@
 class AccionUsuario(enum.Enum):
     """Enumeración de acciones de usuario que pueden desencadenar flujos integrados."""
     REACCIONAR_PUBLICACION = "reaccionar_publicacion"
     ACCEDER_NARRATIVA_VIP = "acceder_narrativa_vip"
     TOMAR_DECISION = "tomar_decision"
     PARTICIPAR_CANAL = "participar_canal"
     VERIFICAR_ENGAGEMENT = "verificar_engagement"
     TEST_EVALUACION_EMOCIONAL = "test_evaluacion_emocional"
+    COMPRAR_ARTICULO = "comprar_articulo"
+    LISTAR_TIENDA = "listar_tienda"
+    VER_INVENTARIO = "ver_inventario"

 class CoordinadorCentral:
@@ .. @@
         # Servicios de integración
         self.channel_engagement = ChannelEngagementService(session)
         self.narrative_point = NarrativePointService(session)
         self.narrative_access = NarrativeAccessService(session)
+        self.shop_integration = ShopIntegrationService(session)
         # Servicios base
         self.narrative_service = NarrativeService(session)
         self.point_service = PointService(session)
@@ .. @@
             elif accion == AccionUsuario.TEST_EVALUACION_EMOCIONAL:
                 return await self._flujo_test_evaluacion_emocional(user_id, **kwargs)
+            elif accion == AccionUsuario.COMPRAR_ARTICULO:
+                return await self._flujo_comprar_articulo(user_id, **kwargs)
+            elif accion == AccionUsuario.LISTAR_TIENDA:
+                return await self._flujo_listar_tienda(user_id, **kwargs)
+            elif accion == AccionUsuario.VER_INVENTARIO:
+                return await self._flujo_ver_inventario(user_id, **kwargs)
             else:
                 logger.warning(f"Acción no implementada: {accion}")
                 return {
@@ .. @@
         return base_message
+    
+    async def _flujo_comprar_articulo(self, user_id: int, item_id: int, bot=None) -> Dict[str, Any]:
+        """
+        Flujo para procesar compra de artículo en tienda.
+        Integra verificación de puntos, acceso VIP y desbloqueo de pistas.
+        """
+        try:
+            # 1. Análisis emocional de la compra (opcional)
+            emotional_context = None
+            if self.emotional_analysis:
+                try:
+                    import datetime
+                    emotional_context = await self.emotional_analysis.analyze_response_timing(
+                        user_id, datetime.datetime.utcnow(), "shop_purchase"
+                    )
+                except Exception as e:
+                    logger.debug(f"Análisis emocional de compra falló para usuario {user_id}: {str(e)}")
+            
+            # 2. Procesar compra a través del servicio de integración
+            purchase_result = await self.shop_integration.process_item_purchase(
+                user_id, item_id, bot
+            )
+            
+            if not purchase_result["success"]:
+                # Compra fallida - Lucien maneja errores como custodio
+                error_message = self.character_voice.get_character_response(
+                    CharacterType.LUCIEN,
+                    EmotionalContext.PAUSA_REFLEXIVA,
+                    "purchase_failed",
+                    emotional_context
+                ) if self.character_voice else purchase_result["message"]
+                
+                return {
+                    "success": False,
+                    "message": f"{error_message}\n\n*{purchase_result['message']}*",
+                    "action": purchase_result["action"],
+                    "emotional_context": emotional_context
+                }
+            
+            # 3. Compra exitosa - Diana celebra la adquisición
+            user_points = await self.point_service.get_user_points(user_id)
+            user_history = {"total_interactions": user_points // 10}
+            
+            emotional_context_enum = self.character_voice.map_emotional_analysis_to_context(
+                emotional_context, emotional_context, None, user_history
+            ) if self.character_voice else EmotionalContext.ENGAGEMENT_ALTO
+            
+            # Diana responde a compras exitosas (momentos de inversión)
+            success_message = self.character_voice.get_character_response(
+                CharacterType.DIANA,
+                emotional_context_enum,
+                "purchase_success",
+                emotional_context,
+                user_history
+            ) if self.character_voice else purchase_result["message"]
+            
+            # Agregar información de la compra
+            purchase_data = purchase_result.get("purchase_data", {})
+            if purchase_data.get("lore_unlocked"):
+                success_message += f"\n\n*🗝️ Has desbloqueado: {purchase_data['lore_unlocked']}*"
+            
+            return {
+                "success": True,
+                "message": success_message,
+                "action": "purchase_completed",
+                "purchase_data": purchase_data,
+                "side_effects": purchase_result.get("side_effects", {}),
+                "emotional_context": emotional_context
+            }
+            
+        except Exception as e:
+            logger.exception(f"Error en flujo de compra para usuario {user_id}: {str(e)}")
+            return {
+                "success": False,
+                "message": "Error inesperado durante la compra. Intenta nuevamente.",
+                "action": "purchase_error",
+                "error": str(e)
+            }
+    
+    async def _flujo_listar_tienda(self, user_id: int, category: str = None, bot=None) -> Dict[str, Any]:
+        """
+        Flujo para mostrar catálogo de tienda personalizado.
+        Integra verificación VIP y recomendaciones personalizadas.
+        """
+        try:
+            # 1. Obtener catálogo personalizado
+            catalog_result = await self.shop_integration.get_personalized_shop_catalog(user_id)
+            
+            if not catalog_result["success"]:
+                # Error obteniendo catálogo - Lucien maneja errores
+                error_message = self.character_voice.get_character_response(
+                    CharacterType.LUCIEN,
+                    EmotionalContext.PAUSA_REFLEXIVA,
+                    "access_denied"
+                ) if self.character_voice else catalog_result["message"]
+                
+                return {
+                    "success": False,
+                    "message": error_message,
+                    "action": "catalog_error"
+                }
+            
+            # 2. Generar mensaje de bienvenida a la tienda
+            user_points = catalog_result["user_points"]
+            is_vip = catalog_result["is_vip"]
+            total_items = catalog_result["total_items"]
+            
+            # Determinar contexto emocional para mensaje de tienda
+            user_history = {"total_interactions": user_points // 5}
+            emotional_context_enum = EmotionalContext.USUARIO_AVANZADO if user_points > 100 else EmotionalContext.NUEVO_USUARIO
+            
+            # Diana presenta la tienda como extensión de su mundo
+            if is_vip:
+                welcome_message = self.character_voice.get_character_response(
+                    CharacterType.DIANA,
+                    EmotionalContext.USUARIO_AVANZADO,
+                    "shop_vip_welcome",
+                    None,
+                    user_history
+                ) if self.character_voice else "Bienvenido a mi tienda exclusiva"
+            else:
+                welcome_message = self.character_voice.get_character_response(
+                    CharacterType.DIANA,
+                    emotional_context_enum,
+                    "shop_welcome",
+                    None,
+                    user_history
+                ) if self.character_voice else "Bienvenido a mi tienda"
+            
+            # Crear mensaje completo de tienda
+            shop_message = f"{welcome_message}\n\n"
+            shop_message += f"🛒 **Mi Tienda Personal**\n\n"
+            shop_message += f"💰 **Tus besitos**: {user_points}\n"
+            shop_message += f"📦 **Artículos disponibles**: {total_items}\n"
+            
+            if is_vip:
+                shop_message += f"💎 **Acceso VIP**: Todos los artículos disponibles\n"
+            else:
+                vip_items = sum(
+                    len([item for item in items if item.get("is_vip_exclusive")])
+                    for items in catalog_result["items_by_category"].values()
+                )
+                if vip_items > 0:
+                    shop_message += f"🔒 **Artículos VIP**: {vip_items} (requiere suscripción)\n"
+            
+            shop_message += f"\n*Cada artículo ha sido elegido cuidadosamente para enriquecer tu experiencia...*"
+            
+            return {
+                "success": True,
+                "message": shop_message,
+                "action": "catalog_displayed",
+                "catalog_data": catalog_result
+            }
+            
+        except Exception as e:
+            logger.exception(f"Error en flujo de listado de tienda para usuario {user_id}: {str(e)}")
+            return {
+                "success": False,
+                "message": "Error cargando la tienda. Intenta nuevamente.",
+                "action": "catalog_error",
+                "error": str(e)
+            }
+    
+    async def _flujo_ver_inventario(self, user_id: int, bot=None) -> Dict[str, Any]:
+        """
+        Flujo para mostrar inventario del usuario.
+        Integra con sistema de pistas narrativas.
+        """
+        try:
+            # 1. Obtener resumen del inventario
+            inventory_summary = await self.shop_integration.get_user_shop_summary(user_id)
+            
+            if not inventory_summary["success"]:
+                return {
+                    "success": False,
+                    "message": inventory_summary["message"],
+                    "action": "inventory_error"
+                }
+            
+            # 2. Generar mensaje de inventario con voz auténtica
+            inventory_count = inventory_summary["inventory_count"]
+            total_spent = inventory_summary["total_spent"]
+            
+            # Lucien presenta el inventario como custodio de posesiones
+            inventory_message = self.character_voice.get_character_response(
+                CharacterType.LUCIEN,
+                EmotionalContext.USUARIO_AVANZADO if inventory_count > 5 else EmotionalContext.NUEVO_USUARIO,
+                "inventory_presentation"
+            ) if self.character_voice else "Tu inventario personal"
+            
+            inventory_text = f"{inventory_message}\n\n"
+            inventory_text += f"📦 **Tu Colección Personal**\n\n"
+            inventory_text += f"🎒 **Artículos**: {inventory_count}\n"
+            inventory_text += f"💸 **Total invertido**: {total_spent} besitos\n"
+            
+            if inventory_summary.get("recent_purchases"):
+                inventory_text += f"\n🛍️ **Compras recientes**:\n"
+                for purchase in inventory_summary["recent_purchases"][:3]:
+                    inventory_text += f"• {purchase['item_name']} ({purchase['price_paid']}💋)\n"
+            
+            return {
+                "success": True,
+                "message": inventory_text,
+                "action": "inventory_displayed",
+                "inventory_data": inventory_summary
+            }
+            
+        except Exception as e:
+            logger.exception(f"Error en flujo de inventario para usuario {user_id}: {str(e)}")
+            return {
+                "success": False,
+                "message": "Error cargando tu inventario.",
+                "action": "inventory_error",
+                "error": str(e)
+            }