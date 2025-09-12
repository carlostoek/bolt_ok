@@ .. @@
 from handlers.admin_narrative_handlers import router as admin_narrative_handlers
 from handlers.test_evaluation_handler import router as test_evaluation_router
+from handlers.shop_handler import router as shop_router
+from handlers.admin.shop_admin import router as admin_shop_router

 import combinar_pistas
 from backpack import router as backpack_router
@@ .. @@
             ("narrative", narrative_router),
             ("admin_narrative", admin_narrative_handlers),
             ("test_evaluation", test_evaluation_router),
+            ("shop", shop_router),
+            ("admin_shop", admin_shop_router),
         ]