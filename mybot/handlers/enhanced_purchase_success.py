            # Enhanced emotional success message
            success_text = f"""💝 **¡Compra Exitosa!**

🌸 **Diana sonríe...** has adquirido: **{item.name}**

💰 *Has invertido {item.price} besitos en algo especial...*
*Tu conexión con Diana acaba de profundizar...*
"""

            # Check if lore was unlocked
            unlocked_lore = result.get("unlocked_lore")
            if unlocked_lore:
                success_text += f"""

🎉 **¡Contenido Íntimo Desbloqueado!**

Diana te revela un nuevo secreto:
📜 **{unlocked_lore['title']}**

_{unlocked_lore.get('description', 'Nuevo contenido disponible')}_

📖 Puedes acceder a este contenido exclusivo desde el menú narrativo.
*Diana espera ansiosa a que lo explores...*
"""

            # Check if narrative fragment was unlocked
            unlocked_fragment = result.get("unlocked_fragment")
            if unlocked_fragment:
                success_text += f"""

📖 **¡Nuevo Capítulo Revelado!**

Diana ha desbloqueado un fragmento especial solo para ti.
📖 Usa "📖 Continuar historia" para sumergirte más profundo en su mundo.
*¿Te atreves a seguir descubriendo sus secretos?*
"""

            success_text += """

🎒 *Tu colección personal acaba de crecer...*
*Gracias por valorar lo que Diana comparte contigo...*"""

            # ========================================
            # MEJORA #2: UPSELL INTELIGENTE POST-COMPRA
            # ========================================

            # Determinar upsell inteligente
            upsell_service = UpsellService(session)
            upsell = await upsell_service.get_smart_upsell(user_id, item)

            # Si hay upsell específico, agregarlo al mensaje
            if upsell["type"] and upsell["message_key"]:
                upsell_message = BOT_MESSAGES.get(upsell["message_key"], "")
                if upsell_message:
                    # Formatear mensaje con datos
                    try:
                        upsell_message = upsell_message.format(**upsell["data"])
                    except KeyError:
                        pass  # Si falta algún dato, usar mensaje sin formatear

                    success_text += f"\n\n─────────────\n\n{upsell_message}"

            # Build keyboard según tipo de upsell
            keyboard = get_upsell_keyboard(
                upsell_type=upsell["keyboard_type"],
                item_data=upsell["keyboard_data"]
            )

            await callback.message.edit_text(
                success_text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            await callback.answer("✨ ¡Compra realizada con amor!", show_alert=False)