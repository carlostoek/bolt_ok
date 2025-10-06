# Plan de Implementación: Sistema de Accesos VIP Gratuitos

## Resumen Ejecutivo

Implementar un sistema para otorgar accesos VIP temporales (generalmente 1 día) a través de:
1. **Hitos narrativos** - Progreso en la historia
2. **Sistema de recompensas** - Canje con besitos en la tienda
3. **Regalos especiales** - Eventos o logros

**Flujo clave**: El sistema genera el token automáticamente, activa el VIP y envía mensaje de bienvenida + link de invitación, sin necesidad de que el usuario ingrese un token manualmente.

---

## Análisis de Componentes Existentes

### 1. Sistema de Tokens Actual (`token_service.py`)
**Funcionalidad existente:**
- `create_vip_token(tariff_id)` - Crea token vinculado a una tarifa
- `activate_token(token_string, user_id)` - Activa token y retorna duración en días
- Marca tokens como usados
- Requiere que usuario ingrese token vía deeplink `/start TOKEN`

**Limitación**: Requiere interacción manual del usuario

### 2. Sistema de Suscripciones (`subscription_service.py`)
**Funcionalidad existente:**
- `extend_subscription(user_id, days)` - Extiende/crea suscripción por X días
- Actualiza `User.role = "vip"` y `User.vip_expires_at`
- Actualiza `VipSubscription.expires_at`
- Logging de operaciones

**Ventaja**: Puede usarse directamente sin necesidad de tokens

### 3. Handler de Activación VIP (`start_token.py`)
**Flujo actual:**
1. Usuario usa `/start TOKEN`
2. Valida token y obtiene duración
3. Crea/actualiza usuario con rol VIP
4. Crea/actualiza suscripción
5. Otorga achievement VIP
6. Genera invite link de 24h al canal VIP
7. Envía mensajes de bienvenida:
   - `BOT_MESSAGES["vip_welcome_special"]` - Mensaje de Señorita Kinky
   - `BOT_MESSAGES["vip_activation_details"]` - Detalles del mayordomo con link

**Ventaja**: Ya tiene toda la lógica de bienvenida implementada

### 4. Sistema de Recompensas (`reward_service.py`)
**Funcionalidad existente:**
- `claim_reward(user_id, reward_id)` - Reclama recompensa
- Valida puntos suficientes
- Marca como reclamada en `UserReward`
- **NO ejecuta ninguna acción**, solo marca como reclamada

**Limitación**: No hay hooks para ejecutar acciones post-reclamación

### 5. Coordinador Central (`coordinador_central.py`)
**Funcionalidad existente:**
- Orquesta integraciones entre módulos
- Define `AccionUsuario` enum para tipos de acciones
- Servicios integrados:
  - `channel_engagement` - Engagement en canales
  - `narrative_point` - Puntos por narrativa
  - `narrative_access` - Acceso a contenido narrativo
  - `point_service` - Gestión de puntos

**Oportunidad**: Punto ideal para centralizar lógica de VIP gratuito

---

## Arquitectura Propuesta

### Componente Central: `VipGrantService`

**Ubicación**: `/services/vip_grant_service.py`

**Responsabilidades**:
1. Otorgar acceso VIP por duración especificada
2. Generar invite link al canal VIP
3. Enviar mensajes de bienvenida automáticos
4. Registrar operación en logs
5. Limpiar cache de roles

**Firma principal**:
```python
async def grant_vip_access(
    user_id: int,
    days: int,
    source: str,  # "narrative", "reward", "gift", "admin"
    source_id: Optional[int] = None,  # fragment_id, reward_id, etc.
    bot: Bot = None
) -> tuple[bool, str]
```

**Retorna**: `(éxito: bool, mensaje: str)`

---

## Puntos de Integración

### 1. **Narrativa** → Coordinador Central

**Archivo**: `services/coordinador_central.py`

**Nueva acción**:
```python
class AccionUsuario(enum.Enum):
    # ... existentes ...
    OTORGAR_VIP_TEMPORAL = "otorgar_vip_temporal"
```

**Nuevo método**:
```python
async def procesar_accion(
    self,
    accion: AccionUsuario,
    user_id: int,
    bot: Bot,
    **kwargs
) -> Dict[str, Any]:
    if accion == AccionUsuario.OTORGAR_VIP_TEMPORAL:
        days = kwargs.get("days", 1)
        source = kwargs.get("source", "narrative")
        source_id = kwargs.get("source_id")

        vip_grant = VipGrantService(self.session)
        success, message = await vip_grant.grant_vip_access(
            user_id=user_id,
            days=days,
            source=source,
            source_id=source_id,
            bot=bot
        )
        return {"success": success, "message": message}
```

**Uso desde fragmentos narrativos**:
```json
{
  "id": 999,
  "text": "Diana te observa con una sonrisa traviesa...",
  "decisions": [],
  "post_actions": [
    {
      "type": "grant_vip",
      "days": 1,
      "source": "narrative",
      "fragment_id": 999
    }
  ]
}
```

### 2. **Recompensas** → Hook Post-Reclamación

**Archivo**: `services/reward_service.py`

**Modificar**: `claim_reward()`

**Agregar después de línea 67**:
```python
# Después de: self.session.add(UserReward(...))
await self.session.commit()

# NUEVO: Ejecutar acción especial si la recompensa es de tipo VIP
if reward.reward_type == "vip_access":
    from services.vip_grant_service import VipGrantService
    vip_grant = VipGrantService(self.session)

    # Extraer duración de metadata o usar default
    days = getattr(reward, 'vip_days', 1)  # Nuevo campo opcional

    success, vip_msg = await vip_grant.grant_vip_access(
        user_id=user_id,
        days=days,
        source="reward",
        source_id=reward.id,
        bot=kwargs.get('bot')  # Pasar bot como kwarg
    )

    if success:
        return True, f"{BOT_MESSAGES['reward_claim_success']}\n\n{vip_msg}"

return True, BOT_MESSAGES.get("reward_claim_success", "Recompensa reclamada")
```

**Modelo**: Agregar campo opcional a `Reward`
```python
# En database/models.py - clase Reward
vip_days = Column(Integer, nullable=True)  # Días VIP si reward_type="vip_access"
```

### 3. **Tienda** → Productos VIP

**Similar a recompensas**, pero en el contexto de productos de tienda.

**Consideración**: Actualmente la tienda usa el modelo `Reward`. Si se quiere diferenciar:
- Opción A: Usar `reward_type = "vip_access"` y campo `vip_days`
- Opción B: Crear modelo separado `StoreProduct` (más trabajo)

**Recomendación**: Opción A por simplicidad

### 4. **Regalos/Achievements** → Integración Directa

**Archivo**: `services/achievement_service.py`

**Para achievements especiales que otorgan VIP**:
```python
async def grant_achievement_reward(
    self,
    user_id: int,
    achievement_id: str,
    bot: Bot
):
    # Lógica actual de achievement...

    # Si el achievement otorga VIP
    achievement_data = ACHIEVEMENTS.get(achievement_id)
    if achievement_data.get("grants_vip"):
        from services.vip_grant_service import VipGrantService
        vip_grant = VipGrantService(self.session)
        await vip_grant.grant_vip_access(
            user_id=user_id,
            days=achievement_data.get("vip_days", 1),
            source="achievement",
            source_id=achievement_id,
            bot=bot
        )
```

---

## Base de Datos

### Nuevas Tablas

#### `vip_grants` - Registro de accesos VIP gratuitos
```sql
CREATE TABLE vip_grants (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    days_granted INT NOT NULL,
    source VARCHAR(50) NOT NULL,  -- 'narrative', 'reward', 'gift', 'admin'
    source_id INT,  -- ID del fragmento, reward, etc.
    granted_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    invite_link VARCHAR(255)
);
```

**Propósito**: Auditoría y analytics de VIPs gratuitos

### Modificaciones a Tablas Existentes

#### `rewards`
```sql
ALTER TABLE rewards
ADD COLUMN vip_days INT;  -- NULL para rewards normales, 1+ para VIP access
```

---

## Mensajes

### Nuevos mensajes en `locales/es.json`

```json
{
  "vip_grant_success": "🎉 *¡Acceso VIP Otorgado!*\n\nHas recibido *{days} día(s)* de acceso VIP.\n\n✨ Disfruta de contenido exclusivo hasta el {expires_at}",

  "vip_grant_narrative": "🎭 *Regalo Narrativo*\n\nComo recompensa por tu elección, Diana te ha otorgado acceso VIP por {days} día(s).",

  "vip_grant_reward": "🎁 *Recompensa Canjeada*\n\n¡Has canjeado tu acceso VIP con éxito!\n\nDuración: {days} día(s)\nExpira: {expires_at}",

  "vip_grant_channel_link": "🔑 *Acceso al Canal VIP*\n\n[Haz clic aquí para unirte]({invite_link})\n\n⏰ Este enlace expira en 24 horas.",

  "vip_grant_error": "❌ No se pudo otorgar el acceso VIP. Por favor contacta a soporte."
}
```

---

## Flujo Completo de Uso

### Escenario 1: Narrativa otorga VIP

```
1. Usuario toma decisión en fragmento narrativo
2. NarrativeService procesa decisión
3. Detecta post_action "grant_vip"
4. Llama a CoordinadorCentral.procesar_accion(OTORGAR_VIP_TEMPORAL)
5. CoordinadorCentral delega a VipGrantService
6. VipGrantService:
   - Extiende suscripción (SubscriptionService)
   - Genera invite link (Bot API)
   - Envía mensajes de bienvenida
   - Registra en vip_grants
7. Usuario recibe:
   - Mensaje de Diana con regalo narrativo
   - Link al canal VIP
   - Detalles de expiración
```

### Escenario 2: Compra en tienda

```
1. Usuario canjea reward "1 Día VIP" (50 besitos)
2. RewardService.claim_reward()
3. Valida puntos y descuenta
4. Detecta reward_type = "vip_access"
5. Llama a VipGrantService.grant_vip_access()
6. VipGrantService ejecuta flujo completo
7. Usuario recibe:
   - Confirmación de canje
   - Activación VIP automática
   - Link de invitación
```

### Escenario 3: Regalo por achievement

```
1. Usuario desbloquea achievement especial
2. AchievementService detecta "grants_vip": true
3. Llama a VipGrantService
4. Usuario recibe VIP + achievement notification
```

---

## Plan de Implementación

### Fase 1: Servicio Core (2-3 horas)
1. ✅ Crear `VipGrantService` con método `grant_vip_access()`
2. ✅ Implementar generación de invite links
3. ✅ Implementar envío de mensajes de bienvenida
4. ✅ Crear tabla `vip_grants` para auditoría
5. ✅ Agregar mensajes a `locales/es.json`

### Fase 2: Integración con Recompensas (1-2 horas)
1. ✅ Agregar campo `vip_days` a modelo `Reward`
2. ✅ Modificar `RewardService.claim_reward()` para detectar `reward_type="vip_access"`
3. ✅ Integrar llamada a `VipGrantService`
4. ✅ Crear recompensa de ejemplo: "1 Día VIP - 50 besitos"

### Fase 3: Integración con Coordinador (1-2 horas)
1. ✅ Agregar `OTORGAR_VIP_TEMPORAL` a `AccionUsuario` enum
2. ✅ Implementar `procesar_accion()` en `CoordinadorCentral`
3. ✅ Documentar formato de `post_actions` en fragmentos narrativos

### Fase 4: Integración con Narrativa (1 hora)
1. ✅ Modificar `NarrativeService` para procesar `post_actions`
2. ✅ Crear fragmento narrativo de ejemplo con VIP grant
3. ✅ Testing de flujo completo

### Fase 5: Testing y Refinamiento (1 hora)
1. ✅ Testing de todos los escenarios
2. ✅ Verificar mensajes y UX
3. ✅ Verificar que links de invitación funcionen
4. ✅ Testing de casos edge (usuario ya VIP, expiración, etc.)

**Tiempo total estimado**: 6-9 horas

---

## Consideraciones Técnicas

### 1. Usuario ya tiene VIP activo
**Solución**: `SubscriptionService.extend_subscription()` ya maneja esto:
- Si VIP activo: suma días a expiración actual
- Si VIP expirado: crea nueva suscripción desde hoy

### 2. Invite links expirados
**Solución**: Links generados son de 24h, suficiente para que usuario se una
- Si expira, usuario puede pedir nuevo link vía soporte

### 3. Bot no tiene permisos para generar invite links
**Solución**: Degradación graceful:
- Intentar generar link
- Si falla, enviar mensaje sin link y notificar admin
- Usuario puede usar link genérico del canal

### 4. Concurrencia (múltiples VIP grants simultáneos)
**Solución**:
- `extend_subscription()` usa transacciones de DB
- Cada grant es atómico
- Días se acumulan correctamente

### 5. Analytics y Reporting
**Tabla `vip_grants`** permite:
- Contar VIPs gratuitos por fuente
- Identificar fragmentos narrativos más generosos
- Medir conversión de VIP gratuito → VIP pagado
- Reportes administrativos

---

## Puntos de Decisión para el Usuario

### 1. ¿Duración por defecto?
**Recomendación**: 1 día para regalos narrativos, configurable para otros

### 2. ¿Límite de VIPs gratuitos por usuario?
**Opciones**:
- A) Sin límite (generoso)
- B) 1 vez por fragmento narrativo (evita farming)
- C) Máximo X días totales de VIP gratuito por mes

**Recomendación**: Opción B - controlar por `vip_grants.source + source_id + user_id` único

### 3. ¿Mensaje diferenciado por fuente?
**Recomendación**: Sí
- Narrativa: Mensaje de Diana explicando el regalo
- Recompensa: Confirmación de canje
- Achievement: Celebración de logro

### 4. ¿Notificar a admins de VIP grants?
**Recomendación**: Solo para monitoreo
- Logging detallado
- Dashboard admin con estadísticas
- No notificaciones en tiempo real (sería spam)

---

## Métricas de Éxito

1. **Tasa de activación**: % de usuarios que usan el invite link en 24h
2. **Conversión VIP**: % de VIP gratuitos que compran VIP después
3. **Engagement**: Comparar actividad durante VIP gratuito vs antes/después
4. **Fuente más efectiva**: Narrativa vs Recompensa vs Achievement
5. **Retención**: % que regresan después de expirar VIP gratuito

---

## Ejemplo de Uso Completo

### Admin crea reward VIP en tienda:
```python
# Script admin
from services.reward_service import RewardService

reward = await reward_service.create_reward(
    title="🔑 1 Día de Acceso VIP",
    description="Acceso completo al canal VIP por 24 horas. Descubre contenido exclusivo de Señorita Kinky.",
    required_points=50,
    reward_type="vip_access",
    vip_days=1
)
```

### Usuario en tienda:
1. Ve "🔑 1 Día de Acceso VIP - 50 besitos"
2. Click en recompensa → Ve detalles
3. Click en "Reclamar" → Descuenta 50 besitos
4. Inmediatamente recibe:
   ```
   🎁 Recompensa Canjeada

   ¡Has canjeado tu acceso VIP con éxito!

   Duración: 1 día(s)
   Expira: 05/10/2025 20:49

   ---

   🎉 ¡Bienvenido al exclusivo mundo VIP!

   [Mensaje especial de Señorita Kinky...]

   ---

   🔑 Acceso al Canal VIP

   [Haz clic aquí para unirte](https://t.me/+ABC123...)

   ⏰ Este enlace expira en 24 horas.
   ```

### En narrativa:
```json
{
  "id": 150,
  "text": "—Has demostrado ser digno de confianza —susurra Diana, acercándose—. Como recompensa... te daré acceso a mi mundo más íntimo. Por un día.",
  "decisions": [],
  "post_actions": [
    {
      "type": "grant_vip",
      "days": 1,
      "source": "narrative",
      "fragment_id": 150
    }
  ],
  "next_fragment_id": 151
}
```

---

## Conclusión

Este sistema permite otorgar VIP gratuito de forma automática, centralizada y auditable desde múltiples puntos del bot (narrativa, tienda, achievements).

El flujo de usuario es fluido: recibe el VIP inmediatamente sin necesidad de tokens manuales, con mensajes contextuales y link directo al canal.

La implementación es modular, reutiliza servicios existentes y mantiene la arquitectura del Coordinador Central como punto de orquestación.
