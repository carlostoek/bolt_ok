# utils/messages.py
"""Centralized texts for the bot."""

# Messages from the Butler of the Divan
BUTLER_MESSAGES = {
    "start_welcome_new_user": (
        "🌙 Bienvenid@ a *El Diván de Diana*…\n\n"
        "Permítame presentarle las maravillas de este lugar. Cada gesto y decisión cuenta en *El Juego del Diván*.\n\n"
        "¿List@ para descubrir lo que le espera? Elija por dónde comenzar y yo me encargaré de guiarle con la debida cortesía."
    ),
    "start_welcome_returning_user": (
        "✨ Me alegra tenerle de regreso.\n\n"
        "Su lugar permanece reservado y sus puntos también. Hay nuevas sorpresas aguardando.\n\n"
        "¿Desea continuar su travesía en *El Juego del Diván*?"
    ),
    "vip_activation_details": (
        "✨ Su membresía VIP ha sido activada por {duration} días.\n"
        "📅 Expira el: {expires_at}\n\n"
        "🔐 A continuación, le presento su invitación personal al Canal VIP.\n"
        "Al hacer clic en el enlace, se unirá automáticamente y de inmediato:\n\n"
        "{invite_link}\n\n"
        "⚠️ Este enlace es exclusivo para usted y expirará en 24 horas.\n"
        "¡Le doy la bienvenida al exclusivo mundo del Diván!"
    ),
    "vip_activation_no_link": (
        "Su membresía VIP ha sido activada por {duration} días.\n"
        "Expira el: {expires_at}.\n\n"
        "Use /vip_menu para acceder a sus beneficios VIP."
    ),
    "vip_members_only": "Esta sección está disponible solo para miembros VIP.",
    "profile_not_registered": "Parece que aún no ha iniciado su recorrido. Use /start para dar su primer paso.",
    "profile_title": "🛋️ *Su rincón en El Diván de Diana*",
    "profile_points": "📌 *Puntos acumulados:* `{user_points}`",
    "profile_level": "🎯 *Nivel actual:* `{user_level}`",
    "profile_points_to_next_level": "📶 *Para el siguiente nivel:* `{points_needed}` más (Nivel `{next_level}` a partir de `{next_level_threshold}`)",
    "profile_max_level": "🌟 Ha alcanzado el nivel más alto. Mis felicitaciones.",
    "profile_achievements_title": "🏅 *Logros desbloqueados*",
    "profile_no_achievements": "Aún no hay logros, pero confío en que los obtendrá.",
    "profile_active_missions_title": "📋 *Sus desafíos activos*",
    "profile_no_active_missions": "Por ahora no hay desafíos disponibles, pero pronto habrá novedades.",
    "ranking_title": "🏆 *Tabla de Posiciones*",
    "ranking_entry": "#{rank}. @{username} - Puntos: `{points}`, Nivel: `{level}`",
    "no_ranking_data": "Aún no hay datos en el ranking. Sea usted el primero en aparecer.",
    "no_active_subscription": "No tiene una suscripción activa.",
}

# Messages from Señorita Kinky
KINKY_MESSAGES = {
    "vip_welcome_special": (
        "Hola, mi Kinky. Qué emoción que estés aquí, donde todo lo especial sucede. "
        "Prepárate, porque este será nuestro rincón secreto. Desde ahora te dejo a cargo de mi querido Mayordomo del Diván, "
        "él cuidará de ti y te llevará de la mano. Pero no te preocupes… seguiré muy, muy cerca."
    ),
    "verify_instagram": "📡 Verificando Instagram...",
    "reconnecting": "🔄 Reintentando conexión...",
    "verified": "✅ ¡Perfecto! Instagram verificado.",
    "gift_unlocked": "✨ ¡Regalo desbloqueado! Aquí tienes una sorpresa para ti solo: [contenido de muestra o enlace al pack gratuito]",
    "PACK_INTEREST_REPLY": "💌 ¡Gracias! Recibí tu interés. Me pondré en contacto contigo muy pronto. O si no quieres esperar escríbeme directo a mi chat privado en ,,@DianaKinky ",
}

# Menu texts and general options
MENU_TEXTS = {
    "FREE_MENU_TEXT": "✨ *Bienvenid@ a mi espacio gratuito*\n\nElige y descubre un poco de mi mundo...",
    "FREE_GIFT_TEXT": "🎁 *Desbloquear regalo*\nActiva tu obsequio de bienvenida y descubre los primeros detalles de todo lo que tengo para ti.",
    "PACKS_MENU_TEXT": (
        "🎀 *Paquetes especiales de Diana* 🎀\n\n"
        "¿Quieres una probadita de mis momentos más intensos?\n\n"
        "Estos son sets que puedes comprar directamente, sin suscripción. Cada uno incluye fotos y videos explícitos. 🥵\n\n"
        "🛍️ Elige tu favorito y presiona *“Me interesa”*. Yo me pondré en contacto contigo."
    ),
    "FREE_VIP_EXPLORE_TEXT": (
        "🔐 *Bienvenido al Diván de Diana* 🔐\n\n"
        "¿Te atreves a entrar a mi universo sin censura?\n\n"
        "✨ Más de 2000 archivos privados\n"
        "🎬 Videos explícitos sin censura\n"
        "🎁 Descuentos en contenido personalizado\n"
        "👀 Acceso exclusivo a mis historias diarias\n\n"
        "📌 Precio: *$350 MXN / mes*"
    ),
    "VIP_INTEREST_REPLY": (
        "💌 ¡Gracias! Recibí tu interés. Me pondré en contacto contigo muy pronto. "
        "O si no quieres esperar escríbeme directo a mi chat privado en ,,@DianaKinky "
    ),
    "FREE_CUSTOM_TEXT": "💌 *Quiero contenido personalizado*\nCuéntame tus fantasías y recibirás algo hecho solo para ti.",
    "FREE_GAME_TEXT": "🎮 *Modo gratuito del juego Kinky*\nDisfruta de un adelanto de la diversión. La versión completa te espera en el VIP.",
    "FREE_FOLLOW_TEXT": "🌐 *¿Dónde más seguirme?*\nEncuentra todos mis enlaces y redes para que no te pierdas nada.",
    "PACK_1_DETAILS": (
        "💫 *Encanto Inicial*\n"
        "Una primera mirada. Una chispa.\n"
        "Aquí comienza el juego entre tú y yo…\n\n"
        "Este set es tu puerta de entrada a mi mundo:\n"
        "📹 1 video íntimo donde mis dedos exploran lentamente mientras mis labios y mirada te envuelven.\n"
        "📸 10 fotos donde apenas cubro lo necesario… lencería suave, piel desnuda, miradas insinuantes.\n\n"
        "Perfecto si quieres conocerme de una forma dulce, coqueta y provocadora.\n\n"
        "*150 MXN (10 USD)*"
    ),
    "PACK_2_DETAILS": (
        "🔥 *Sensualidad Revelada*\n"
        "Te muestro más. Te invito a quedarte…\n\n"
        "Este set revela lo que solo pocos han visto:\n"
        "📹 2 videos donde me toco sin censura, jugando con mi cuerpo mientras mi rostro refleja cada sensación.\n"
        "📸 10 fotos tan provocadoras que te harán dudar si mirar una sola vez será suficiente.\n\n"
        "Es mi manera de decirte:\n"
        "“No es lo que ves... es cómo te lo muestro.”\n\n"
        "*200 MXN (14 USD)*"
    ),
    "PACK_3_DETAILS": (
        "💋 *Pasión Desbordante*\n"
        "Aquí ya no hay timidez. Solo deseo.\n\n"
        "Este set está hecho para quienes quieren ver *todo* lo que puedo provocar:\n"
        "📹 3 videos:\n"
        "1. En lencería de alto voltaje\n"
        "2. Vestida, pero seduciéndote con juegos visuales\n"
        "3. Jugando con un juguetito que me hace gemir suave… y fuerte.\n"
        "📸 15 fotos íntimas y provocativas, capturadas en el punto exacto entre arte y placer.\n\n"
        "Un set para perderte y volver a verme... muchas veces.\n\n"
        "*250 MXN (17 USD)*"
    ),
    "PACK_4_DETAILS": (
        "🔞 *Intimidad Explosiva*\n\n"
        "Esto no es un set. Es una confesión explícita…\n\n"
        "Mi lado más sucio, más real, más entregado:\n"
        "📹 5 videos:\n"
        "- Me masturbo hasta acabar... sin cortes.\n"
        "- Uso dildos, me abro, gimo, me muerdo los labios.\n"
        "- Me desvisto lentamente hasta estar completamente desnuda.\n"
        "- Juego con mis juguetes favoritos.\n"
        "- Y uno… donde estoy montando, moviéndome como si estuvieras debajo. Sin censura.\n\n"
        "📸 15 fotos extra, como regalo. Fotos que no circulan por ningún otro lado.\n\n"
        "Este es el set que convierte la fantasía en algo real.\n"
        "Lo más explícito. Lo más mío. Lo más tuyo.\n\n"
        "*300 MXN (20 USD)*"
    ),
}

# Mission and minigame messages
MISSION_MESSAGES = {
    "missions_title": "🎯 *Desafíos disponibles*",
    "missions_no_active": "No hay desafíos por el momento. Aproveche para tomar aliento.",
    "mission_not_found": "Ese desafío no existe o ya expiró.",
    "mission_already_completed": "Ya lo completó. Excelente trabajo.",
    "mission_completed_success": "✅ ¡Desafío completado! Ganó `{points_reward}` puntos.",
    "mission_completed_feedback": "🎉 ¡Misión '{mission_name}' completada! Ganó `{points_reward}` puntos.",
    "mission_level_up_bonus": "🚀 Ha subido de nivel. Ahora está en el nivel `{user_level}`. Las aventuras serán más emocionantes.",
    "mission_achievement_unlocked": "\n🏆 Logro desbloqueado: *{achievement_name}*",
    "mission_completion_failed": "❌ No pudimos registrar este desafío. Verifique si ya lo completó antes o si aún está activo.",
    "reward_shop_title": "🎁 *Recompensas del Diván*",
    "reward_shop_empty": "Por ahora no hay recompensas disponibles. Pero pronto sí.",
    "reward_not_found": "Esa recompensa ya no está disponible.",
    "reward_not_registered": "Su perfil no está activo. Use /start para comenzar *El Juego del Diván*.",
    "reward_not_enough_points": "Le faltan `{required_points}` puntos. Actualmente tiene `{user_points}`.",
    "reward_claim_success": "🎉 ¡Recompensa reclamada!",
    "reward_claim_failed": "No pudimos procesar su solicitud.",
    "reward_already_claimed": "Esta recompensa ya fue reclamada.",
    "level_up_notification": "🎉 ¡Subió a Nivel {level}: {level_name}! {reward}",
    "special_level_reward": "✨ Recompensa especial por alcanzar el nivel {level}! {reward}",
    "menu_missions_text": "Aquí están los desafíos que puede emprender. ¡Cada uno le acerca más!",
    "menu_rewards_text": "¡Es momento de canjear sus puntos! Estas son las recompensas disponibles:",
    "confirm_purchase_message": "¿Está segur@ de que desea canjear {reward_name} por {reward_cost} puntos?",
    "purchase_cancelled_message": "Compra cancelada. Puede seguir explorando otras recompensas.",
    "gain_points_instructions": "Puede ganar puntos completando misiones y participando en las actividades del canal.",
    "points_total_notification": "Ahora tiene {total_points} puntos acumulados.",
    "checkin_success": "✅ Check-in registrado. Ganó {points} puntos.",
    "checkin_already_done": "Ya realizó su check-in. Vuelva mañana.",
    "daily_gift_received": "🎁 Recibió {points} puntos del regalo diario!",
    "daily_gift_already": "Ya reclamó el regalo diario. Vuelva mañana.",
    "daily_gift_disabled": "Regalos diarios deshabilitados.",
    "minigames_disabled": "Minijuegos deshabilitados.",
    "dice_points": "Ganó {points} puntos lanzando el dado.",
    "trivia_correct": "¡Correcto! +5 puntos",
    "trivia_wrong": "Respuesta incorrecta.",
    "reaction_registered_points": "✅ Reacci\u00f3n registrada. Ganaste {points} puntos.",
    "reaction_already": "Ya has reaccionado a este post.",
    "enter_reward_name": "Ingresa el nombre de la recompensa:",
    "enter_reward_points": "Ingresa los puntos necesarios para esta recompensa:",
    "invalid_number": "Por favor, ingresa un número válido.",
    "enter_reward_description": "Ingresa la descripción de la recompensa:",
    "select_reward_type": "Selecciona el tipo de recompensa:",
    "reward_created": "✅ Recompensa creada exitosamente.",
    "reward_deleted": "✅ Recompensa eliminada exitosamente.",
    "reward_updated": "✅ Recompensa actualizada exitosamente.",
    "level_created": "✅ Nivel creado exitosamente.",
    "level_updated": "✅ Nivel actualizado exitosamente.",
    "level_deleted": "✅ Nivel eliminado exitosamente.",
    "weekly_ranking_title": "🏅 Ranking Semanal de Reacciones",
    "weekly_ranking_entry": "#{rank}. @{username} - {count} reacciones",
    "challenge_started": "Reto iniciado! Reacciona a {count} publicaciones para ganar puntos.",
    "mission_details_text": (
        "🎯 *{mission_name}*\n"
        "{mission_description}\n\n"
        "🏆 Recompensa: {points_reward} puntos\n"
        "🗂 Tipo: {mission_type}"
    ),
    "view_all_missions_button_text": "📋 Ver Todas las Misiones",
}

# Aggregate all messages for backward compatibility
BOT_MESSAGES = {
    **BUTLER_MESSAGES,
    **KINKY_MESSAGES,
    **MENU_TEXTS,
    **MISSION_MESSAGES,
}

# Badge descriptions
BADGE_TEXTS = {
    "first_message": {
        "name": "Primer Mensaje",
        "description": "Envía tu primer mensaje en el chat",
    },
    "conversador": {
        "name": "Conversador",
        "description": "Alcanza 100 mensajes enviados",
    },
    "invitador": {
        "name": "Invitador",
        "description": "Consigue 5 invitaciones exitosas",
    },
}

NIVEL_TEMPLATE = """
🎮 Tu nivel actual: {current_level}
✨ Puntos totales: {points}
📊 Progreso hacia el siguiente nivel: {percentage:.1%}
🎯 Te faltan {points_needed} puntos para alcanzar el nivel {next_level}.
"""
TRIVIA_INTRO_MESSAGE = "🎲 *Selecciona una trivia:*"
TRIVIA_COMPLETE_MESSAGE = "🎉 *Has completado la trivia con {score} respuestas correctas.*"
TRIVIA_ADMIN_MENU = "🛠️ *Panel de Administración de Trivias*"

# ============================================================================
# MONETIZATION MESSAGES - Sprint 1: Conversion Focus
# ============================================================================

# Besitos Packs Messages
BESITOS_MESSAGES = {
    "besitos_packs_intro": (
        "💰 **¿Tan cerca y tan lejos?**\n\n"
        "*Lucien te mira con comprensión*\n\n"
        "—Solo te faltan **{missing} besitos** para conseguir lo que deseas...\n\n"
        "💡 Tengo dos opciones para ti:\n\n"
        "**1️⃣ Comprar besitos ahora** (instantáneo)\n"
        "   └─> Packs desde $50 MXN, con bonos incluidos\n\n"
        "**2️⃣ Ganar besitos gratis** (toma tiempo)\n"
        "   └─> Completa misiones y vuelve\n\n"
        "*Diana no espera a nadie... ¿qué decides?* 😏"
    ),

    "besitos_pack_1_details": (
        "💋 **Pack Básico**\n\n"
        "**500 besitos** por solo **$50 MXN**\n\n"
        "Perfecto para:\n"
        "• Comprar 1-2 items de tienda\n"
        "• Desbloquear fragmentos narrativos\n"
        "• Participar en subastas pequeñas\n\n"
        "*Lucien puede ayudarte con el pago* 💳"
    ),

    "besitos_pack_2_details": (
        "💋💋 **Pack Premium**\n\n"
        "**1,000 besitos + 100 GRATIS** por **$90 MXN**\n\n"
        "*¡El más popular!*\n\n"
        "Ideal para:\n"
        "• Comprar varios items premium\n"
        "• Pujar en subastas importantes\n"
        "• Desbloquear múltiples niveles\n\n"
        "**Bonus:** +10% gratis = 1,100 besitos totales\n\n"
        "*Diana recomienda este pack* 😉"
    ),

    "besitos_pack_3_details": (
        "💋💋💋 **Pack Luxury**\n\n"
        "**2,500 besitos + 500 GRATIS** por **$200 MXN**\n\n"
        "*Para los más dedicados*\n\n"
        "Con esto puedes:\n"
        "• Acceder a TODO el contenido premium\n"
        "• Dominar subastas sin límites\n"
        "• Desbloquear finales secretos\n\n"
        "**Bonus:** +20% gratis = 3,000 besitos totales\n\n"
        "*El pack de los verdaderos players* 👑"
    ),

    "besitos_interest_reply": (
        "💌 **Solicitud Recibida**\n\n"
        "*Lucien asiente*\n\n"
        "—Excelente elección. Diana me pidió que coordine tu compra.\n\n"
        "📱 Te contactaré en breve para el pago, o puedes escribirme directo:\n"
        "WhatsApp: @DianaKinky\n\n"
        "*Tus besitos llegarán en minutos* ⚡"
    ),

    "besitos_packs_bonus_intro": (
        "🎉 **¡Oferta Especial!**\n\n"
        "*Diana está impresionada con tu actividad*\n\n"
        "Por tu lealtad, te ofrezco un **bonus exclusivo**:\n\n"
        "💝 **+30% EXTRA en cualquier pack**\n\n"
        "Ejemplos:\n"
        "• $50 → 650 besitos (normal 500)\n"
        "• $90 → 1,430 besitos (normal 1,100)\n"
        "• $200 → 3,900 besitos (normal 3,000)\n\n"
        "⏰ *Oferta válida solo HOY*"
    ),
}

# Session Individual Messages
SESSION_MESSAGES = {
    "session_standard_offer": (
        "💋 **Sesión Individual con Diana**\n\n"
        "*Lucien te mira con una sonrisa cómplice*\n\n"
        "—Diana quiere conocerte más allá de la pantalla.\n"
        "Una conexión más... personal.\n\n"
        "**Lo que incluye:**\n"
        "• Videollamada privada 30 minutos\n"
        "• Contenido personalizado para ti\n"
        "• Experiencia única e íntima\n"
        "• Audio/video que solo tú tendrás\n\n"
        "**Inversión:** $500 MXN\n\n"
        "*Solo 3 espacios disponibles este mes* 🔒"
    ),

    "session_vip_special_offer": (
        "👑 **Oferta Exclusiva VIP**\n\n"
        "*Diana te reservó algo especial*\n\n"
        "Como miembro VIP activo, tienes acceso a:\n\n"
        "💋 **Sesión Individual Premium**\n"
        "• 30 minutos solo tú y Diana\n"
        "• Contenido personalizado según tus fantasías\n"
        "• Pack de fotos/videos exclusivos post-sesión\n\n"
        "~~$800 MXN~~ **$500 MXN** (VIP Price)\n\n"
        "*Cupos limitados, prioridad para VIPs* ✨"
    ),

    "session_loyalty_discount": (
        "🎁 **Regalo de Lealtad**\n\n"
        "Has sido un miembro increíble.\n"
        "Diana quiere agradecerte personalmente.\n\n"
        "💝 **Sesión Individual con Descuento**\n"
        "• Videollamada privada 30 min\n"
        "• Contenido hecho para ti\n"
        "• Experiencia inolvidable\n\n"
        "~~$800 MXN~~ **$400 MXN**\n"
        "*Solo para miembros de 60+ días*\n\n"
        "¿Aceptas la invitación de Diana? 💋"
    ),

    "session_emotional_narrative": (
        "💫 **Diana te sintió...**\n\n"
        "*Ese fragmento que acabas de vivir fue intenso, ¿verdad?*\n\n"
        "Diana quiere conocerte más allá de la pantalla.\n"
        "Conectar contigo de manera más... personal.\n\n"
        "💋 **Sesión Individual Privada**\n"
        "• 30 minutos solo tú y Diana\n"
        "• Videollamada íntima y personalizada\n"
        "• Contenido creado especialmente para ti\n\n"
        "**Inversión:** $500 MXN\n"
        "*Solo 3 espacios disponibles este mes*\n\n"
        "¿Te atreves a cruzar la pantalla? 🔥"
    ),

    "session_interest_reply": (
        "💌 **Solicitud Enviada**\n\n"
        "*Diana recibió tu mensaje personal.*\n\n"
        "Lucien se pondrá en contacto contigo en las próximas horas\n"
        "para coordinar tu sesión privada.\n\n"
        "📞 **También puedes escribir directamente:**\n"
        "WhatsApp: @DianaKinky\n\n"
        "*Te esperamos* 💋"
    ),

    "session_high_auction_offer": (
        "🏆 **¡Ganaste!** Y Diana lo notó.\n\n"
        "*Pujaste {auction_value} besitos...*\n"
        "*Eso demuestra que sabes lo que quieres.*\n\n"
        "Diana reserva sus sesiones individuales\n"
        "para quienes realmente aprecian su tiempo.\n\n"
        "💋 **Oferta Exclusiva para Ti**\n"
        "Sesión privada de 30 min con Diana\n\n"
        "**Precio VIP:** $500 MXN\n"
        "*Cupo limitado, solo este mes*\n\n"
        "Lucien puede coordinar todo por ti. 📞"
    ),
}

# Post-Purchase Upsell Messages
UPSELL_MESSAGES = {
    "upsell_premium_pack_vip": (
        "📸 *Diana susurra:*\n\n"
        "—Ya que estás desbloqueando secretos...\n"
        "¿te gustaría el pack fotográfico completo?\n\n"
        "**Pack Sensualidad Revelada** - $200 MXN\n"
        "• 15 fotos exclusivas HD\n"
        "• Behind the scenes\n"
        "• Video mensaje personal de Diana\n\n"
        "*Solo para quien desbloqueó este fragmento* 🔥"
    ),

    "upsell_vip_upgrade_free": (
        "💎 *Lucien nota tu entusiasmo*\n\n"
        "—Veo que te gusta lo que ofrece Diana...\n"
        "Tienes {points} besitos acumulados.\n\n"
        "¿Sabías que con VIP obtienes:\n"
        "• 50% de descuento en TODO\n"
        "• Contenido diario exclusivo\n"
        "• Sets completos (no teasers)\n\n"
        "**Oferta especial:** Primera semana GRATIS\n"
        "*Solo por comprar hoy* 🎁"
    ),

    "upsell_session_loyal_vip": (
        "👑 *{username}, tu ausencia se nota*\n\n"
        "Diana guarda contenido exclusivo solo para ti.\n"
        "Has sido un miembro increíble ({days_vip} días).\n\n"
        "¿Qué tal una sesión individual?\n"
        "**Precio especial HOY:** $400 MXN (50% desc)\n\n"
        "*Por tu lealtad* 💝"
    ),

    "upsell_besitos_reload_active": (
        "🎉 *¡Wow! Tercera compra del día!*\n\n"
        "Diana está impresionada con tu entusiasmo.\n\n"
        "💝 **Regalo especial:**\n"
        "Recarga besitos ahora y recibe **30% EXTRA gratis**\n\n"
        "Ejemplo:\n"
        "• Pack 1000 besitos → Recibes 1,300\n"
        "• Pack 2500 besitos → Recibes 3,250\n\n"
        "*Oferta válida solo hoy* ⏰"
    ),
}

# VIP Products in Shop
VIP_PRODUCTS_MESSAGES = {
    "vip_day_offer": (
        "✨ **Acceso VIP por 1 Día**\n\n"
        "*Lucien te ofrece una prueba*\n\n"
        "¿Quieres experimentar el mundo VIP sin compromiso?\n\n"
        "**24 horas de acceso completo:**\n"
        "• Todo el contenido exclusivo\n"
        "• Descuentos en tienda\n"
        "• Acceso a subastas VIP\n\n"
        "**Precio:** $50 MXN (1 día)\n\n"
        "*Perfecto para probar antes de comprometerte* 💎"
    ),

    "vip_month_offer": (
        "💎 **Membresía VIP - 1 Mes Completo**\n\n"
        "*El acceso total al mundo de Diana*\n\n"
        "**Lo que obtienes:**\n"
        "• Acceso ilimitado a +2000 archivos\n"
        "• Videos sin censura diarios\n"
        "• 50% descuento en tienda\n"
        "• Prioridad en subastas\n"
        "• Sets completos (no teasers)\n\n"
        "**Precio:** $350 MXN (30 días)\n\n"
        "*La mejor inversión en placer* 🔥"
    ),

    "vip_interest_standard": (
        "💌 **Solicitud de VIP Recibida**\n\n"
        "*Lucien prepara tu acceso*\n\n"
        "—Excelente decisión. Diana te dará la bienvenida.\n\n"
        "Te contactaré en breve para activar tu membresía.\n"
        "O escríbeme directo: @DianaKinky\n\n"
        "*Tu acceso VIP estará listo en minutos* ✨"
    ),
}

# ============================================================================
# EMPTY STATES MOTIVACIONALES - QUICK WIN
# ============================================================================

EMPTY_STATES_MESSAGES = {
    "missions_empty": {
        "title": "🎯 Sin desafíos activos",
        "message": "Por ahora no hay desafíos disponibles, pero pronto habrá novedades.\n\n💡 **¿Qué puedes hacer?**\n• Revisa tu progreso en /profile\n• Explora la narrativa con /start\n• Visita la tienda con /shop",
        "cta": "📖 Continuar historia"
    },
    "achievements_empty": {
        "title": "🏅 Tu colección de logros",
        "message": "Aún no hay logros, pero confío en que los obtendrás.\n\n✨ **Próximos logros disponibles:**\n• **Primer paso**: Envía tu primer mensaje\n• **Explorador**: Completa 3 fragmentos narrativos\n• **Social**: Reacciona a 5 publicaciones",
        "cta": "🎭 Comenzar aventura"
    },
    "shop_empty": {
        "title": "🛍️ Tienda temporalmente vacía",
        "message": "Por ahora no hay recompensas disponibles. Pero pronto sí.\n\n💎 **Próximamente:**\n• Contenido exclusivo de Diana\n• Accesos VIP temporales\n• Sesiones personalizadas\n\n💝 Mientras tanto, acumula besitos completando misiones.",
        "cta": "📋 Ver misiones"
    },
    "inventory_empty": {
        "title": "🎒 Tu mochila está vacía",
        "message": "Aún no has coleccionado items especiales.\n\n🔮 **Cómo obtener items:**\n• Completa misiones desafiantes\n• Participa en eventos especiales\n• Desbloquea finales secretos\n• Gana subastas exclusivas",
        "cta": "🎯 Buscar misiones"
    },
    "ranking_empty": {
        "title": "🏆 Sé el primero en liderar",
        "message": "Aún no hay datos en el ranking. Sea usted el primero en aparecer.\n\n⚡ **Cómo subir en el ranking:**\n• Completa misiones diarias\n• Reacciona a publicaciones\n• Invita amigos al canal\n• Participa en eventos",
        "cta": "⭐ Ganar puntos"
    }
}

def get_empty_state_message(context: str, user_points: int = 0) -> str:
    """Obtiene un mensaje motivacional para estados vacíos"""
    empty_data = EMPTY_STATES_MESSAGES.get(context, {
        "title": "📭 Sin contenido",
        "message": "No hay elementos para mostrar en este momento.",
        "cta": "🏠 Menú principal"
    })
    
    message = f"**{empty_data['title']}**\n\n{empty_data['message']}"
    
    # Personalizar basado en puntos del usuario
    if user_points > 0 and context == "shop_empty":
        message += f"\n\n💰 **Tienes {user_points} besitos listos para gastar**"
    
    return message

def get_empty_state_cta(context: str) -> str:
    """Obtiene el CTA para el estado vacío"""
    return EMPTY_STATES_MESSAGES.get(context, {}).get("cta", "🏠 Menú principal")

# Admin Notifications (for internal tracking)
ADMIN_NOTIFICATION_TEMPLATES = {
    "besitos_interest": (
        "💰 **INTERÉS EN PAQUETE DE BESITOS**\n\n"
        "**Usuario:** {first_name} (@{username})\n"
        "**ID:** {user_id}\n"
        "**Pack:** {pack_name} - ${price} MXN\n"
        "**Besitos:** {besitos}\n"
        "**Contexto:** {context}\n\n"
        "Contactar para coordinar pago."
    ),

    "session_interest": (
        "💋 **SOLICITUD DE SESIÓN INDIVIDUAL**\n\n"
        "**Usuario:** {first_name} (@{username})\n"
        "**ID:** {user_id}\n"
        "**Tipo sesión:** {session_type}\n"
        "**VIP desde:** {vip_since}\n"
        "**Besitos actuales:** {points}\n"
        "**Trigger:** {trigger_reason}\n\n"
        "Contactar para coordinar sesión."
    ),

    "vip_interest": (
        "💎 **INTERÉS EN MEMBRESÍA VIP**\n\n"
        "**Usuario:** {first_name} (@{username})\n"
        "**ID:** {user_id}\n"
        "**Tipo:** {vip_type}\n"
        "**Días activo:** {days_active}\n"
        "**Besitos:** {points}\n\n"
        "Contactar para activar VIP."
    ),
}

# ============================================================================
# LOADING STATES CONTEXTUALES - QUICK WIN
# ============================================================================

LOADING_MESSAGES = {
    "emotional_analysis": [
        "💭 Diana está analizando tus emociones...",
        "🔍 Lucien estudia tu respuesta con atención...",
        "🎭 Detectando los matices en tu mensaje...",
        "✨ Tu esencia está siendo procesada..."
    ],
    "archetype_detection": [
        "🎯 Identificando tu arquetipo dominante...",
        "🔮 Diana busca patrones en tu personalidad...",
        "📊 Analizando tus elecciones anteriores...",
        "💫 Tu esencia única está siendo revelada..."
    ],
    "content_loading": [
        "📸 Preparando contenido especial para ti...",
        "🎁 Diana selecciona algo perfecto...",
        "✨ Cargando momentos mágicos...",
        "💋 Preparando sorpresas sensuales..."
    ],
    "narrative_progression": [
        "📖 Avanzando en tu historia personal...",
        "🎭 Diana prepara el siguiente fragmento...",
        "✨ Tu camino se desvela...",
        "💫 Transicionando a nuevas experiencias..."
    ],
    "general_processing": [
        "⚡ Procesando tu solicitud...",
        "💭 Diana está pensando...",
        "✨ Trabajando en tu respuesta...",
        "🎯 Preparando algo especial..."
    ]
}

def get_loading_message(context: str) -> str:
    """Obtiene un mensaje de loading contextual aleatorio"""
    import random
    messages = LOADING_MESSAGES.get(context, LOADING_MESSAGES["general_processing"])
    return random.choice(messages)

# Update BOT_MESSAGES with new categories
BOT_MESSAGES.update(BESITOS_MESSAGES)
BOT_MESSAGES.update(SESSION_MESSAGES)
BOT_MESSAGES.update(UPSELL_MESSAGES)
BOT_MESSAGES.update(VIP_PRODUCTS_MESSAGES)
BOT_MESSAGES.update(LOADING_MESSAGES)
