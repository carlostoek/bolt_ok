@@ .. @@
         [
             InlineKeyboardButton(text="🎯 Misiones", callback_data="menu:missions"),
+            InlineKeyboardButton(text="🛒 Tienda", callback_data="menu:shop")
-            InlineKeyboardButton(text="🎁 Regalo Diario", callback_data="daily_gift")
         ],
         [
+            InlineKeyboardButton(text="🎁 Regalo Diario", callback_data="daily_gift"),
             InlineKeyboardButton(text="🏆 Mi Perfil", callback_data="menu:profile"),
-            InlineKeyboardButton(text="🗺️ Mochila", callback_data="open_backpack")
         ],
         [
+            InlineKeyboardButton(text="🗺️ Mochila", callback_data="open_backpack"),
             InlineKeyboardButton(text="💝 Recompensas", callback_data="menu:rewards"),
-            InlineKeyboardButton(text="👑 Ranking", callback_data="menu:ranking")
         ],
+        [
+            InlineKeyboardButton(text="👑 Ranking", callback_data="menu:ranking"),
+            InlineKeyboardButton(text="📦 Inventario", callback_data="menu:shop_inventory")
+        ],
         [InlineKeyboardButton(text="🏛️ Subastas", callback_data="auction_main")],