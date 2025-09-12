@@ .. @@
 def get_free_main_menu_kb() -> InlineKeyboardMarkup:
     """Return the main menu keyboard for free users."""
     builder = InlineKeyboardBuilder()
     builder.button(text="📖 Historia", callback_data="start_narrative")
+    builder.button(text="🛒 Tienda", callback_data="menu:shop")
     builder.button(text="🎁 Desbloquear Regalo", callback_data="free_gift")
     builder.button(text="🎀 Mis Packs", callback_data="free_packs")
     builder.button(text="🔐 Explorar VIP", callback_data="free_vip_explore")
     builder.button(text="💌 Contenido Custom", callback_data="free_custom")
     builder.button(text="🎮 Juego Kinky", callback_data="free_game")
     builder.button(text="🌐 Sígueme", callback_data="free_follow")
-    builder.adjust(1, 2, 2, 2)
+    builder.adjust(2, 2, 2, 2)
     return builder.as_markup()