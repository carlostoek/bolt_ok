@@ .. @@
         elif message_type == "daily_already_done":
             return f"{base_response}\n\n*\"Ya hemos compartido hoy, mi amor. Dale tiempo al deseo de crecer...\"*"
         elif message_type.startswith("participation_"):
             action = message_type.split("_")[1] if "_" in message_type else "actividad"
             return f"{base_response}\n\n*Observo tu {action} con interés creciente...*"
+        elif message_type == "purchase_success":
+            return f"{base_response}\n\n*\"Cada elección que haces en mi tienda revela más sobre tus deseos...\"*"
+        elif message_type == "shop_welcome":
+            return f"{base_response}\n\n*\"Bienvenido a mi colección personal. Cada artículo tiene una historia...\"*"
+        elif message_type == "shop_vip_welcome":
+            return f"{base_response}\n\n*\"Ah, mi querido VIP... aquí tienes acceso a mis tesoros más íntimos...\"*"
         else:
             return base_response
@@ .. @@
         elif message_type == "guidance":
             co_creation = random.choice(self.lucien_patterns.CO_CREACION_FOCUS)
             return f"{co_creation}\n\n{base_response}"
+        elif message_type == "purchase_failed":
+            return f"{base_response}\n\n*\"Algunas adquisiciones requieren más preparación. Cultiva tus recursos primero.\"*"
+        elif message_type == "inventory_presentation":
+            return f"{base_response}\n\n*\"Permíteme mostrarle su colección personal. Cada objeto cuenta una historia.\"*"
         else:
             return base_response