"""
Mensajes de onboarding para usuarios gratuitos del canal.
Narrados por Lucien, el mayordomo del Diván de Diana.
"""

def get_join_request_message(wait_minutes: int, social_links: dict) -> tuple[str, list]:
    """
    Mensaje inicial cuando el usuario solicita unirse al canal gratuito.

    Args:
        wait_minutes: Tiempo de espera en minutos
        social_links: Dict con enlaces sociales {'instagram': 'url', 'tiktok': 'url', etc}

    Returns:
        tuple: (mensaje_texto, lista_de_botones_inline)
    """
    if wait_minutes >= 60:
        hours = wait_minutes // 60
        remaining_minutes = wait_minutes % 60
        if remaining_minutes > 0:
            wait_text = f"{hours} {'hora' if hours == 1 else 'horas'} y {remaining_minutes} minutos"
        else:
            wait_text = f"{hours} {'hora' if hours == 1 else 'horas'}"
    else:
        wait_text = f"{wait_minutes} minutos"

    message = f"""🎩 **Bienvenido al Diván de Diana**

Permítame presentarme. Soy **Lucien**, el mayordomo de este distinguido establecimiento.

Su solicitud para acceder al canal gratuito ha sido **registrada exitosamente**.

⏰ **Tiempo de espera estimado**: {wait_text}

Mientras tanto, permítame sugerirle algo que podría acelerar considerablemente su entrada...

💫 **Diana** tiene presencia en otras plataformas donde comparte contenido exclusivo. Seguirla en sus redes sociales no solo le permitirá conocerla mejor, sino que también **demostrará su genuino interés**.

_Los usuarios que siguen a Diana suelen recibir una bienvenida más... personalizada._

Utilice los botones a continuación para visitarla:"""

    # Construir botones inline
    buttons = []

    if social_links.get('instagram'):
        buttons.append({
            'text': '📸 Instagram',
            'url': social_links['instagram']
        })

    if social_links.get('tiktok'):
        buttons.append({
            'text': '🎵 TikTok',
            'url': social_links['tiktok']
        })

    if social_links.get('twitter'):
        buttons.append({
            'text': '🐦 Twitter/X',
            'url': social_links['twitter']
        })

    if social_links.get('onlyfans'):
        buttons.append({
            'text': '🔞 OnlyFans',
            'url': social_links['onlyfans']
        })

    return message, buttons


def get_welcome_approved_message(username: str = None) -> str:
    """
    Mensaje de bienvenida cuando el usuario es aprobado en el canal.

    Args:
        username: Nombre del usuario (opcional)
    """
    greeting = f"**{username}**" if username else "estimado invitado"

    return f"""🎉 **¡Excelente noticia!**

{greeting}, su solicitud ha sido **aprobada**.

Ya tiene acceso completo al canal gratuito del Diván de Diana.

Ahora, permítame presentarle formalmente a la dueña de este establecimiento...

---

🌸 **Diana te da la bienvenida**

_Hola, mi kinky. Qué emoción que estés aquí._

_Este es mi espacio, donde lo especial sucede. Aquí encontrarás contenido gratuito, pero también... mucho más._

_Si quieres conocerme de verdad, tienes dos opciones:_

💎 **Modo VIP**: Acceso completo a todo mi contenido sin censura, videos explícitos, historias diarias y descuentos especiales.

📖 **La Historia**: Una experiencia narrativa única donde tus decisiones importan. Gana besitos, desbloquea contenido y descubre secretos.

---

🎩 **Lucien nuevamente**

¿Por dónde desea comenzar su experiencia en el Diván?

Use el menú principal del bot para explorar todas las opciones disponibles."""


def get_reminder_follow_socials(wait_remaining: int, social_links: dict) -> tuple[str, list]:
    """
    Recordatorio amigable para seguir en redes sociales mientras espera.

    Args:
        wait_remaining: Minutos restantes de espera
        social_links: Dict con enlaces sociales

    Returns:
        tuple: (mensaje_texto, lista_de_botones_inline)
    """
    message = f"""🎩 **Lucien aquí, nuevamente**

Veo que aún está esperando su aprobación.

⏰ Tiempo restante aproximado: **{wait_remaining} minutos**

Permítame recordarle que seguir a Diana en sus redes sociales no solo le mantendrá entretenido durante la espera, sino que también demuestra su compromiso.

_Los usuarios que muestran interés genuino suelen tener una experiencia más... enriquecedora._

¿Ya la siguió en todas sus plataformas?"""

    buttons = []

    if social_links.get('instagram'):
        buttons.append({
            'text': '📸 Instagram',
            'url': social_links['instagram']
        })

    if social_links.get('tiktok'):
        buttons.append({
            'text': '🎵 TikTok',
            'url': social_links['tiktok']
        })

    return message, buttons


def get_onboarding_start_message() -> str:
    """
    Mensaje inicial del onboarding después de ser aprobado en el canal.
    Introduce al usuario a las opciones disponibles.
    """
    return """🌟 **Comencemos su recorrido**

Permítame explicarle las opciones disponibles en el Diván:

📖 **La Historia**
Una narrativa interactiva donde sus decisiones moldean la experiencia. Gane besitos completando fragmentos, desbloquee contenido exclusivo y descubra los secretos de Diana.

🎁 **Contenido Gratuito**
Acceso a packs de muestra, regalos exclusivos y adelantos de lo que Diana tiene para ofrecer.

💎 **Membresía VIP**
La experiencia completa y sin censura. Más de 2000 archivos privados, videos explícitos, descuentos en contenido personalizado y acceso a historias diarias.

🛒 **La Tienda**
Use sus besitos para comprar productos exclusivos que desbloquean más contenido narrativo y experiencias especiales.

---

¿Por dónde le gustaría comenzar? Use los botones del menú principal para explorar."""


# Enlaces de redes sociales (configurables)
DEFAULT_SOCIAL_LINKS = {
    'instagram': 'https://instagram.com/dianakinky',
    'tiktok': 'https://tiktok.com/@dianakinky',
    'twitter': 'https://twitter.com/dianakinky',
    'onlyfans': 'https://onlyfans.com/dianakinky'
}
