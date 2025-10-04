# Ejemplos de Uso: Sistema de VIP Gratuito

Este documento muestra ejemplos prácticos de cómo usar el sistema de VIP gratuito en diferentes contextos.

---

## 1. Desde la Tienda (Recompensas con Besitos)

### Crear recompensa VIP en la tienda

```python
from services.reward_service import RewardService

async def crear_reward_vip_1_dia(session):
    """Crea una recompensa de 1 día VIP canjeable con besitos."""
    reward_service = RewardService(session)

    reward = await reward_service.create_reward(
        title="🔑 1 Día de Acceso VIP",
        description=(
            "Descubre el mundo exclusivo de Diana por 24 horas.\n\n"
            "Incluye:\n"
            "✨ Acceso al canal VIP\n"
            "🎬 Más de 2000 archivos privados\n"
            "🎁 Descuentos especiales\n\n"
            "¡Prueba el lujo del Diván!"
        ),
        required_points=50,  # Cuesta 50 besitos
        reward_type="vip_access",  # Tipo especial
    )

    # Establecer duración VIP
    reward.vip_days = 1
    await session.commit()

    print(f"✓ Recompensa VIP creada: ID {reward.id}")
    return reward
```

### Cuando usuario canjea la recompensa

El sistema automáticamente:
1. Descuenta 50 besitos
2. Activa VIP por 1 día
3. Genera invite link al canal
4. Envía mensajes de bienvenida

**Código interno** (ya implementado en `RewardService.claim_reward()`):
```python
# El usuario ve en el menú:
# "🔑 1 Día de Acceso VIP - 50 besitos"

# Click en "Reclamar" →

# Sistema internamente hace:
success, message = await reward_service.claim_reward(
    user_id=user_id,
    reward_id=reward_id,
    bot=bot  # ← Importante: pasar bot
)

# Si reward.reward_type == "vip_access":
#   → Llama a VipGrantService
#   → Activa VIP automáticamente
#   → Envía mensajes
```

**Usuario recibe:**
```
🎁 Recompensa Canjeada

¡Has canjeado tu acceso VIP con éxito!

📅 Duración: 1 día(s)
⏰ Expira: 05/10/2025 21:30

✨ El Diván te espera...

---

[Mensaje de Señorita Kinky]

---

🔑 Acceso al Canal VIP

[Haz clic aquí para unirte](https://t.me/+ABC123...)

⏰ Este enlace expira en 24 horas.
```

---

## 2. Desde la Narrativa (Post-Actions en Fragmentos)

### Fragmento narrativo que otorga VIP

```json
{
  "id": 250,
  "text": "Diana se acerca, sus ojos brillan con complicidad.\n\n—Has demostrado valor y lealtad —susurra—. Como recompensa, te abriré las puertas de mi círculo más íntimo. Por un día, serás parte de mi mundo oculto.\n\nSus dedos rozan tu mano.",
  "decisions": [
    {
      "id": 1,
      "text": "Aceptar el regalo con gratitud",
      "next_fragment_id": 251,
      "points": 10
    },
    {
      "id": 2,
      "text": "Preguntar qué significa \"mundo oculto\"",
      "next_fragment_id": 252,
      "points": 5
    }
  ],
  "post_actions": [
    {
      "type": "grant_vip",
      "days": 1,
      "source": "narrative",
      "fragment_id": 250
    }
  ],
  "vip_required": false
}
```

### Procesar fragment con post_action

```python
from services.coordinador_central import CoordinadorCentral, AccionUsuario

async def procesar_fragmento_con_vip_grant(user_id: int, fragment: dict, bot):
    """Procesa un fragmento narrativo que otorga VIP."""

    # ... usuario ve el fragmento y toma decisión ...

    # Procesar post_actions
    if "post_actions" in fragment:
        coordinador = CoordinadorCentral(session)

        for action in fragment["post_actions"]:
            if action.get("type") == "grant_vip":
                # Otorgar VIP vía Coordinador Central
                resultado = await coordinador.ejecutar_flujo(
                    user_id=user_id,
                    accion=AccionUsuario.OTORGAR_VIP_TEMPORAL,
                    days=action.get("days", 1),
                    source="narrative",
                    source_id=action.get("fragment_id"),
                    bot=bot
                )

                if resultado["success"]:
                    # Notificar al usuario
                    await bot.send_message(
                        user_id,
                        resultado["message"]
                    )
```

---

## 3. Desde Achievements (Logros Especiales)

### Achievement que otorga VIP

```python
# En services/achievement_service.py - ACHIEVEMENTS dict

ACHIEVEMENTS = {
    "narrative_master": {
        "id": "narrative_master",
        "name": "Maestro de la Narrativa",
        "description": "Completa todos los capítulos del Level 1",
        "icon": "📚",
        "points": 100,
        "grants_vip": True,  # ← Nuevo campo
        "vip_days": 1,       # ← Días a otorgar
        "criteria": {
            "type": "fragments_completed",
            "min_count": 50
        }
    }
}
```

### Otorgar achievement con VIP

```python
from services.achievement_service import AchievementService
from services.coordinador_central import CoordinadorCentral, AccionUsuario

async def grant_achievement_with_vip(user_id: int, achievement_id: str, bot, session):
    """Otorga achievement y VIP si aplica."""

    # Otorgar achievement normal
    ach_service = AchievementService(session)
    granted = await ach_service.grant_achievement(user_id, achievement_id, bot=bot)

    if granted:
        # Verificar si otorga VIP
        achievement_data = ACHIEVEMENTS.get(achievement_id, {})

        if achievement_data.get("grants_vip"):
            coordinador = CoordinadorCentral(session)
            days = achievement_data.get("vip_days", 1)

            resultado = await coordinador.ejecutar_flujo(
                user_id=user_id,
                accion=AccionUsuario.OTORGAR_VIP_TEMPORAL,
                days=days,
                source="achievement",
                source_id=achievement_id,
                bot=bot
            )

            # Usuario recibe:
            # 1. Notificación de achievement
            # 2. Mensajes de VIP grant
            # 3. Invite link al canal
```

---

## 4. Desde Admin (Manual)

### Admin otorga VIP a usuario específico

```python
from services.coordinador_central import CoordinadorCentral, AccionUsuario

async def admin_grant_vip(admin_id: int, target_user_id: int, days: int, bot, session):
    """Admin otorga VIP manualmente a un usuario."""

    # Verificar que quien ejecuta es admin
    from utils.user_roles import get_user_role
    role = await get_user_role(bot, admin_id, session=session)

    if role != "admin":
        return {"success": False, "message": "Solo administradores pueden hacer esto"}

    coordinador = CoordinadorCentral(session)
    resultado = await coordinador.ejecutar_flujo(
        user_id=target_user_id,
        accion=AccionUsuario.OTORGAR_VIP_TEMPORAL,
        days=days,
        source="admin",
        source_id=admin_id,  # ID del admin que otorgó
        bot=bot
    )

    if resultado["success"]:
        # Notificar al admin
        await bot.send_message(
            admin_id,
            f"✓ VIP otorgado a usuario {target_user_id} por {days} días"
        )

        # Usuario recibe automáticamente los mensajes de VIP

    return resultado
```

---

## 5. Auditoría y Analytics

### Consultar grants de un usuario

```python
from services.vip_grant_service import VipGrantService

async def ver_historial_vip_grants(user_id: int, session):
    """Muestra historial de VIP grants de un usuario."""

    vip_grant = VipGrantService(session)
    grants = await vip_grant.get_user_grants(user_id)

    for grant in grants:
        print(f"""
        Grant #{grant.id}
        - Días: {grant.days_granted}
        - Fuente: {grant.source}
        - Otorgado: {grant.granted_at}
        - Expira: {grant.expires_at}
        """)
```

### Analytics: VIP grants por fuente

```python
async def analytics_vip_grants_por_fuente(session):
    """Muestra estadísticas de VIP grants por fuente."""

    vip_grant = VipGrantService(session)

    sources = ["narrative", "reward", "achievement", "admin"]

    for source in sources:
        grants = await vip_grant.get_grants_by_source(source, limit=1000)
        print(f"{source}: {len(grants)} grants")

        # Calcular días totales otorgados
        total_days = sum(g.days_granted for g in grants)
        print(f"  Total días: {total_days}")
```

### Verificar duplicados (anti-farming)

```python
async def puede_recibir_grant_narrativo(user_id: int, fragment_id: int, session):
    """Verifica si usuario ya recibió VIP de este fragmento."""

    vip_grant = VipGrantService(session)

    ya_recibio = await vip_grant.check_duplicate_grant(
        user_id=user_id,
        source="narrative",
        source_id=fragment_id
    )

    if ya_recibio:
        return False, "Ya recibiste el VIP de este capítulo"

    return True, "OK"
```

---

## 6. Flujo Completo: Usuario Compra Reward VIP

```python
async def flujo_completo_compra_vip(user_id: int, bot, session):
    """Simula el flujo completo cuando usuario compra reward VIP."""

    # 1. Usuario navega a tienda
    # 2. Ve reward: "🔑 1 Día de Acceso VIP - 50 besitos"
    # 3. Click en reward

    reward_id = 123  # ID del reward VIP

    # 4. Sistema ejecuta claim
    from services.reward_service import RewardService
    reward_service = RewardService(session)

    success, message = await reward_service.claim_reward(
        user_id=user_id,
        reward_id=reward_id,
        bot=bot
    )

    # 5. Sistema internamente:
    #    a. Valida puntos (50 besitos)
    #    b. Descuenta puntos
    #    c. Detecta reward_type="vip_access"
    #    d. Llama a VipGrantService
    #    e. VipGrantService:
    #       - Extiende suscripción por 1 día
    #       - Genera invite link (24h)
    #       - Envía mensajes de bienvenida
    #       - Registra en vip_grants
    #       - Limpia cache de roles

    # 6. Usuario recibe:
    #    - Confirmación de canje
    #    - Mensaje de Diana
    #    - Link al canal VIP

    # 7. Usuario click en link → Se une al canal automáticamente

    # 8. En 24 horas:
    #    - VIP expira
    #    - Scheduler lo remueve del canal
    #    - Usuario puede comprar de nuevo si quiere

    return success, message
```

---

## 7. Mensajes que Recibe el Usuario

### Desde Tienda (Reward)

```
🎁 Recompensa Canjeada

¡Has canjeado tu acceso VIP con éxito!

📅 Duración: 1 día(s)
⏰ Expira: 05/10/2025 21:30

✨ El Diván te espera...
```

```
Hola, mi Kinky. Qué emoción que estés aquí, donde todo lo especial sucede...
[Mensaje completo de Señorita Kinky]
```

```
🔑 Acceso al Canal VIP

[Haz clic aquí para unirte](https://t.me/+ABC123...)

⏰ Este enlace expira en 24 horas.
```

### Desde Narrativa

```
🎭 Regalo Narrativo

Como recompensa por tu elección, Diana te ha otorgado acceso VIP por 1 día(s).

—Que disfrutes los secretos que guardé para ti —susurra Diana con una sonrisa cómplice.
```

```
[Mensaje de bienvenida de Señorita Kinky]
```

```
🔑 Acceso al Canal VIP
...
```

### Desde Achievement

```
🏆 ¡Logro Desbloqueado!

Como recompensa por tu dedicación, has recibido 1 día(s) de acceso VIP.

Diana aplaude suavemente: —Lo has ganado.
```

```
[Mensaje de bienvenida...]
```

---

## 8. Configuración de Productos VIP

### Diferentes duraciones

```python
# 1 día - Prueba
await reward_service.create_reward(
    title="🔑 Prueba VIP - 1 Día",
    description="Prueba el mundo VIP por 24 horas",
    required_points=50,
    reward_type="vip_access",
    vip_days=1
)

# 3 días - Fin de semana
await reward_service.create_reward(
    title="🔑 Weekend VIP - 3 Días",
    description="Disfruta el fin de semana en el mundo VIP",
    required_points=120,
    reward_type="vip_access",
    vip_days=3
)

# 7 días - Semana completa
await reward_service.create_reward(
    title="🔑 Semana VIP Completa",
    description="Una semana entera de acceso exclusivo",
    required_points=250,
    reward_type="vip_access",
    vip_days=7
)
```

---

## Notas Importantes

1. **Bot requerido**: Siempre pasar `bot` al llamar a servicios que otorgan VIP
2. **Invite links**: Se generan automáticamente, expiran en 24h
3. **Acumulación**: Si usuario ya tiene VIP, los días se suman
4. **Auditoría**: Todos los grants quedan registrados en `vip_grants`
5. **Anti-farming**: Usar `check_duplicate_grant()` para prevenir abuse
6. **Roles**: El cache de roles se limpia automáticamente
7. **Expiración**: El scheduler de VIP se encarga de remover usuarios expirados

---

## Testing

```python
# Test de grant básico
await coordinador.ejecutar_flujo(
    user_id=123456,
    accion=AccionUsuario.OTORGAR_VIP_TEMPORAL,
    days=1,
    source="admin",
    bot=bot
)

# Verificar en DB
from database.models import VipGrant
stmt = select(VipGrant).where(VipGrant.user_id == 123456)
result = await session.execute(stmt)
grant = result.scalar_one_or_none()

assert grant is not None
assert grant.days_granted == 1
assert grant.source == "admin"
```
