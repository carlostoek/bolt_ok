"""
Mensajes CTA (Call To Action) para usuarios FREE

Estos mensajes se muestran cuando usuarios gratuitos intentan acceder a
contenido/funciones VIP. Están diseñados con el tono de Diana/Señorita Kinky
para generar deseo y conversión.

Estrategia:
- Tono seductor pero respetuoso
- Generar FOMO (Fear Of Missing Out)
- Mostrar lo que se están perdiendo
- Invitar de forma natural a ser VIP
"""

import random

# ═══════════════════════════════════════════════════════════════════════════════
# CTAs GENERALES - Para cualquier contenido VIP bloqueado
# ═══════════════════════════════════════════════════════════════════════════════

GENERAL_VIP_CTAS = [
    {
        "message": (
            "💎 **Oh, mi amor...**\n\n"
            "Me encantaría mostrarte esto, pero este contenido es exclusivo para quienes "
            "están más cerca de mí en **El Diván**.\n\n"
            "✨ Los VIP tienen acceso a todo lo que tengo para ofrecer... "
            "¿Te gustaría descubrirlo?"
        ),
        "button_text": "💎 Quiero ser VIP"
    },
    {
        "message": (
            "🌹 **Eres especial, pero...**\n\n"
            "Este es un espacio íntimo, reservado solo para mis VIP. "
            "Allí comparto cosas que no verás en ningún otro lugar.\n\n"
            "¿Listo para conocer mi lado más auténtico?"
        ),
        "button_text": "🔥 Acceder al Diván"
    },
    {
        "message": (
            "💋 **Mmm... no tan rápido**\n\n"
            "Lo que buscas está detrás de una puerta que solo se abre "
            "para quienes realmente quieren estar cerca de mí.\n\n"
            "En **El Diván VIP** te espero con mucho más... mucho más íntimo."
        ),
        "button_text": "✨ Desbloquear acceso"
    },
]

# ═══════════════════════════════════════════════════════════════════════════════
# CTAs ESPECÍFICOS POR FUNCIÓN
# ═══════════════════════════════════════════════════════════════════════════════

VIP_CTA_SHOP = {
    "message": (
        "🛍️ **La Tienda Secreta de Diana**\n\n"
        "Veo que has encontrado mi colección especial... Te gusta lo que ves, ¿verdad?\n\n"
        "Aquí están mis **{total_items} tesoros exclusivos**: diarios íntimos, polaroids secretas, "
        "audios sensuales y mucho más.\n\n"
        "💎 Pero solo mis VIP pueden llevarlos. ¿Quieres ser uno de ellos?"
    ),
    "button_text": "💝 Quiero acceder a la tienda"
}

VIP_CTA_MISSIONS = {
    "message": (
        "🎯 **Misiones del Diván**\n\n"
        "Aquí está todo lo que puedes hacer para ganarte mis besitos y atención...\n\n"
        "Veo **{total_missions} misiones** esperándote, desde las más simples hasta "
        "las más... intensas. 😏\n\n"
        "✨ Pero solo mis VIP pueden completarlas y ganar recompensas especiales.\n\n"
        "¿Te animas a jugar conmigo?"
    ),
    "button_text": "🔓 Desbloquear misiones"
}

VIP_CTA_AUCTIONS = {
    "message": (
        "🏛️ **Subastas Exclusivas**\n\n"
        "Cada semana ofrezco algo único en subasta: contenido nunca visto, "
        "experiencias personalizadas, momentos irrepetibles.\n\n"
        "Mis VIP compiten por estas joyas... y siempre hay sorpresas.\n\n"
        "💎 ¿Quieres participar en la próxima?"
    ),
    "button_text": "👑 Unirme a las subastas"
}

VIP_CTA_BACKPACK = {
    "message": (
        "🗺️ **Tu Mochila de Secretos**\n\n"
        "Aquí guardarías todas las pistas, fragmentos de mi diario y tesoros "
        "que vas desbloqueando...\n\n"
        "Pero para coleccionar estos secretos, primero necesitas estar en **El Diván**.\n\n"
        "Cada pieza cuenta una historia. ¿Quieres conocerlas todas?"
    ),
    "button_text": "🔑 Comenzar a coleccionar"
}

VIP_CTA_SHOP_ITEM = {
    "message": (
        "💎 **{item_name}**\n\n"
        "{item_description}\n\n"
        "💰 **Precio:** {item_price} besitos\n\n"
        "Este es uno de mis favoritos... pero solo mis VIP pueden adquirirlo.\n\n"
        "En **El Diván** ganarás besitos completando misiones, "
        "y podrás canjearlos por tesoros como este."
    ),
    "button_text": "💝 Quiero obtenerlo"
}

VIP_CTA_MISSION_COMPLETE = {
    "message": (
        "🎯 **{mission_name}**\n\n"
        "{mission_description}\n\n"
        "⭐ **Recompensa:** {mission_reward} besitos\n\n"
        "Esta misión te está esperando... junto con muchas más.\n\n"
        "Pero solo mis VIP pueden ganar besitos y desbloquear mis secretos. "
        "¿Quieres empezar a jugar?"
    ),
    "button_text": "🎮 Empezar a ganar besitos"
}

VIP_CTA_CONTENT = {
    "message": (
        "📂 **Mi Contenido Exclusivo**\n\n"
        "Esto es lo que mis VIP encuentran dentro de **El Diván**:\n\n"
        "🎀 **Mis Packs:** Colecciones temáticas de fotos y videos\n"
        "💎 **Explorar VIP:** Acceso a +2,000 archivos exclusivos\n"
        "💌 **Contenido Custom:** Pide lo que quieras, yo lo creo para ti\n\n"
        "Todo esto y mucho más está esperándote del otro lado..."
    ),
    "button_text": "🔥 Ver todo el contenido"
}

VIP_CTA_REWARDS = {
    "message": (
        "💝 **Recompensas Especiales**\n\n"
        "Cuando acumulas besitos en **El Diván**, puedes canjearlos por:\n\n"
        "✨ Contenido exclusivo que nunca verás en otro lugar\n"
        "🎁 Experiencias personalizadas solo para ti\n"
        "💌 Acceso anticipado a mis nuevas creaciones\n"
        "🔥 Y muchas sorpresas más...\n\n"
        "Pero primero necesitas estar dentro. ¿Vienes?"
    ),
    "button_text": "💎 Desbloquear recompensas"
}

# ═══════════════════════════════════════════════════════════════════════════════
# CTAs PERSONALIZADOS POR ARQUETIPO
# ═══════════════════════════════════════════════════════════════════════════════

# CTAs generales personalizados por arquetipo
ARCHETYPE_GENERAL_CTAS = {
    "adventurer": {
        "message": (
            "🔥 **Sin Rodeos**\n\n"
            "Veo que no eres de los que pierde el tiempo. Perfecto.\n\n"
            "Aquí está la verdad: todo lo que buscas está del otro lado. "
            "Sin esperas, sin juegos. Directo.\n\n"
            "**El Diván VIP** te da acceso inmediato a todo. ¿Listo?"
        ),
        "button_text": "🔓 Desbloquear ahora"
    },
    "romantic": {
        "message": (
            "💭 **Para Quienes Saben Esperar**\n\n"
            "Aprecio que te tomes tu tiempo... que disfrutes cada momento.\n\n"
            "Pero hay una intimidad que solo se revela cuando cruzas el umbral. "
            "Historias más profundas. Momentos que valen la pena saborear.\n\n"
            "¿Quieres conocer esa parte de mí?"
        ),
        "button_text": "💝 Descubrir más"
    },
    "balanced": {
        "message": (
            "⚖️ **Equilibrio Perfecto**\n\n"
            "Encuentras el balance entre fantasía y realidad. Lo veo.\n\n"
            "**El Diván VIP** te ofrece exactamente eso: contenido que mezcla "
            "narrativa con intimidad real. Lo mejor de ambos mundos.\n\n"
            "¿Te interesa explorar?"
        ),
        "button_text": "✨ Ver qué incluye"
    },
    "explorer": {
        "message": (
            "🎭 **Para los Curiosos**\n\n"
            "Siempre buscando, siempre explorando. Me gusta eso.\n\n"
            "**El Diván VIP** es un universo completo: +2,000 archivos, "
            "packs temáticos, contenido custom... cada rincón tiene algo nuevo.\n\n"
            "¿Listo para descubrirlo todo?"
        ),
        "button_text": "🗺️ Explorar El Diván"
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN HELPER PARA OBTENER CTA (MEJORADA CON ARQUETIPOS)
# ═══════════════════════════════════════════════════════════════════════════════

def get_vip_cta(cta_type: str = "general", archetype: str = None, **context) -> dict:
    """
    Obtiene un mensaje CTA para usuarios free, personalizado por arquetipo.

    Args:
        cta_type: Tipo de CTA (general, shop, missions, etc.)
        archetype: Código de arquetipo ("adventurer", "romantic", "balanced", "explorer")
                   Si se provee, personaliza el CTA según el arquetipo
        **context: Variables para formatear el mensaje

    Returns:
        dict con 'message' y 'button_text'
    """
    # Si hay arquetipo y es CTA general, usar versión personalizada
    if archetype and cta_type == "general" and archetype in ARCHETYPE_GENERAL_CTAS:
        cta = ARCHETYPE_GENERAL_CTAS[archetype].copy()
    # CTAs específicos por tipo
    elif cta_type == "general":
        cta = random.choice(GENERAL_VIP_CTAS)
    elif cta_type == "shop":
        cta = VIP_CTA_SHOP.copy()
    elif cta_type == "missions":
        cta = VIP_CTA_MISSIONS.copy()
    elif cta_type == "auctions":
        cta = VIP_CTA_AUCTIONS.copy()
    elif cta_type == "backpack":
        cta = VIP_CTA_BACKPACK.copy()
    elif cta_type == "shop_item":
        cta = VIP_CTA_SHOP_ITEM.copy()
    elif cta_type == "mission_complete":
        cta = VIP_CTA_MISSION_COMPLETE.copy()
    elif cta_type == "content":
        cta = VIP_CTA_CONTENT.copy()
    elif cta_type == "rewards":
        cta = VIP_CTA_REWARDS.copy()
    else:
        cta = random.choice(GENERAL_VIP_CTAS)

    # Formatear mensaje con contexto si se proporciona
    if context and "{" in cta["message"]:
        try:
            cta["message"] = cta["message"].format(**context)
        except KeyError:
            pass  # Si falta alguna variable, dejar sin formatear

    return cta
