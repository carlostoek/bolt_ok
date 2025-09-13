@@ .. @@
         elif menu_state == "ranking":
             return await create_ranking_menu(user_id, session)
         
+        elif menu_state == "shop":
+            return await self._create_shop_menu(user_id, session)
+        elif menu_state == "shop_inventory":
+            return await self._create_inventory_menu(user_id, session)
+        
         elif menu_state == "narrative":
             return await self._create_narrative_menu(user_id, session)
@@ .. @@
         
         return text, get_narrative_stats_keyboard()
     
+    async def _create_shop_menu(self, user_id: int, session: AsyncSession) -> Tuple[str, InlineKeyboardMarkup]:
+        """Create the shop menu for a user."""
+        from services.coordinador_central import CoordinadorCentral, AccionUsuario
+        from keyboards.shop_kb import get_shop_main_kb
+        
+        try:
+            coordinador = CoordinadorCentral(session)
+            result = await coordinador.ejecutar_flujo(
+                user_id,
+                AccionUsuario.LISTAR_TIENDA
+            )
+            
+            if result["success"]:
+                return result["message"], get_shop_main_kb(result.get("catalog_data", {}))
+            else:
+                return result["message"], get_shop_main_kb({})
+                
+        except Exception as e:
+            logger.error(f"Error creating shop menu for user {user_id}: {e}")
+            return (
+                "❌ **Error Temporal**\n\nNo se pudo cargar la tienda.",
+                get_shop_main_kb({})
+            )
+    
+    async def _create_inventory_menu(self, user_id: int, session: AsyncSession) -> Tuple[str, InlineKeyboardMarkup]:
+        """Create the inventory menu for a user."""
+        from services.coordinador_central import CoordinadorCentral, AccionUsuario
+        from keyboards.shop_kb import get_shop_inventory_kb
+        
+        try:
+            coordinador = CoordinadorCentral(session)
+            result = await coordinador.ejecutar_flujo(
+                user_id,
+                AccionUsuario.VER_INVENTARIO
+            )
+            
+            if result["success"]:
+                inventory_data = result.get("inventory_data", {})
+                return result["message"], get_shop_inventory_kb(inventory_data.get("inventory", []))
+            else:
+                return result["message"], get_shop_inventory_kb([])
+                
+        except Exception as e:
+            logger.error(f"Error creating inventory menu for user {user_id}: {e}")
+            return (
+                "❌ **Error Temporal**\n\nNo se pudo cargar tu inventario.",
+                get_shop_inventory_kb([])
+            )
+    
     def _create_fallback_menu(self, role: str = "free") -> Tuple[str, InlineKeyboardMarkup]: