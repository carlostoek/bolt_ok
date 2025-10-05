# Sesión de Desarrollo: Sistema de Menús y Narrativa
**Fecha**: 2025-10-01
**Duración**: Sesión completa
**Enfoque**: Correcciones de bugs, mejoras al sistema de menús, narrativa y onboarding

---

## Índice
1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Bugs Corregidos](#bugs-corregidos)
3. [Sistema de Menús](#sistema-de-menús)
4. [Sistema de Narrativa](#sistema-de-narrativa)
5. [Sistema de Onboarding](#sistema-de-onboarding)
6. [Scheduler de Suscripciones VIP](#scheduler-de-suscripciones-vip)
7. [Archivos Modificados](#archivos-modificados)
8. [Testing](#testing)

---

## Resumen Ejecutivo

### Problemas Principales Resueltos
1. ✅ Verificación de requisitos de decisiones narrativas (besitos/rol)
2. ✅ Otorgamiento de puntos del fragmento inicial
3. ✅ Menú contextual según rol de usuario (VIP vs Gratuito)
4. ✅ Suscripciones VIP sin fecha de expiración
5. ✅ Sistema de mensajes de requisitos bloqueados
6. ✅ Onboarding completo para canal gratuito

### Nuevas Funcionalidades
1. 🆕 Mensajes detallados cuando faltan requisitos para decisiones
2. 🆕 Sistema de onboarding con voz de Lucien y Diana
3. 🆕 Verificación de estado de solicitud de canal en tiempo real
4. 🆕 Menús dinámicos según rol de usuario

---

## Bugs Corregidos

### 1. Error en `event_admin.py` - Parámetro `session` Faltante

**Problema**:
```python
# handlers/admin/event_admin.py:67
async def start_create_event(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id, session):  # ❌ session no definido
```

**Solución**:
Agregado `session: AsyncSession` como parámetro a 6 funciones:
- `start_create_event()`
- `process_event_name()`
- `process_event_description()`
- `start_create_raffle()`
- `raffle_name()`
- `raffle_desc()`

**Archivo**: `handlers/admin/event_admin.py`

```python
# ✅ Correcto
async def start_create_event(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
```

---

### 2. Claves Faltantes en `BOT_MESSAGES`

**Problema**:
```python
# game_admin.py:764
await callback.message.edit_text(
    BOT_MESSAGES["enter_reward_name"],  # ❌ Key no existe
)
```

**Solución**:
Agregadas 11 claves faltantes en `utils/messages.py`:

```python
MISSION_MESSAGES = {
    # ... existentes ...
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
}
```

**Archivo**: `utils/messages.py`

---

## Sistema de Menús

### Problema: Menú Incorrecto al Regresar desde Narrativa

**Contexto**:
- Usuario gratuito entra a la narrativa
- Usuario presiona "🏠 Menú" para regresar
- **Bug**: El sistema mostraba el menú VIP (con opciones bloqueadas)
- **Esperado**: Mostrar el menú gratuito correspondiente

### Causa Raíz

El callback `narrative_main_menu` usaba un teclado estático sin verificar el rol del usuario:

```python
# ❌ ANTES (main_menu.py)
@router.callback_query(F.data == "narrative_main_menu")
async def return_to_main_menu(callback: CallbackQuery, session: AsyncSession):
    await callback.message.edit_text(
        "🏠 **Menú Principal**\n\n¿Qué deseas hacer?",
        reply_markup=get_main_menu_keyboard()  # ❌ Siempre el mismo menú
    )
```

### Solución Implementada

Modificado para usar `MenuFactory` que crea menús dinámicos según el rol:

```python
# ✅ DESPUÉS (main_menu.py)
@router.callback_query(F.data == "narrative_main_menu")
async def return_to_main_menu(callback: CallbackQuery, session: AsyncSession):
    """Regresa al menú principal según el rol del usuario"""
    user_id = callback.from_user.id

    try:
        # Usar menu factory para crear menú apropiado según rol
        from utils.menu_factory import MenuFactory

        menu_factory = MenuFactory()
        text, keyboard = await menu_factory.create_menu("main", user_id, session, callback.bot)

        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error returning to main menu for user {user_id}: {e}", exc_info=True)
        # Fallback a menú simple
        await callback.message.edit_text(
            "🏠 **Menú Principal**\n\n¿Qué deseas hacer?",
            reply_markup=get_main_menu_keyboard()
        )
        await callback.answer()
```

### Arquitectura de Menús

```
MenuFactory (utils/menu_factory.py)
    ├── _create_main_menu()
    │   ├── role == "admin" → get_admin_main_kb()
    │   ├── role == "vip"   → get_vip_main_kb()
    │   └── role == "free"  → get_free_main_menu_kb()
    │
    └── create_menu(menu_state, user_id, session, bot)
        └── Retorna: (texto, teclado)
```

### Menús Disponibles

#### 1. Menú Gratuito (`get_free_main_menu_kb()`)
```python
# keyboards/subscription_kb.py
- 📖 Historia
- 🎁 Desbloquear Regalo
- 🎀 Mis Packs
- 🔐 Explorar VIP
- 💌 Contenido Custom
- 🎮 Juego Kinky
- 🌐 Sígueme
```

#### 2. Menú VIP (`get_vip_main_kb()`)
```python
- 📖 Historia
- 🏆 Mi Perfil
- 💎 Mi Diván
- 🎯 Misiones
- 🎁 Regalo
- 🛒 Tienda
- 🏛️ Subastas
- 🗺️ Mochila
- 💝 Recompensas
- 👑 Ranking
```

#### 3. Menú Administrador (`get_admin_main_kb()`)
```python
- Panel completo de administración
```

### Flujo Completo

```
Usuario Gratuito:
1. /start → MenuFactory detecta role="free"
2. Muestra get_free_main_menu_kb()
3. Usuario entra a "📖 Historia"
4. Usuario termina y presiona "🏠 Menú"
5. MenuFactory detecta role="free"
6. ✅ Regresa a get_free_main_menu_kb()

Usuario VIP:
1. /start → MenuFactory detecta role="vip"
2. Muestra get_vip_main_kb()
3. Usuario navega libremente
4. Siempre ve opciones VIP
```

---

## Sistema de Narrativa

### 1. Verificación de Requisitos de Decisiones

#### Problema Original

El sistema verificaba los requisitos del **fragmento de destino** en lugar de los requisitos de la **decisión**:

```python
# ❌ ANTES
async def _process_decision_by_id(self, user_id: int, decision_id: int):
    # ...
    if not await self._check_access_conditions(user_id, next_fragment):
        # Verifica fragment.min_besitos y fragment.required_role
        return None
```

**Consecuencia**: Las decisiones configuradas con `required_besitos=0` eran bloqueadas si el fragmento de destino tenía requisitos.

#### Solución

Crear método específico para verificar requisitos de **decisiones**:

```python
# ✅ DESPUÉS
async def _check_decision_requirements(self, user_id: int, decision) -> tuple[bool, dict]:
    """
    Verifica si el usuario cumple los requisitos de una decisión.

    Returns:
        tuple: (can_proceed: bool, requirements_info: dict)
    """
    requirements_info = {
        "missing_besitos": 0,
        "current_besitos": 0,
        "required_besitos": 0,
        "missing_role": None,
        "current_role": "free",
        "required_role": None
    }

    user = await self.session.get(User, user_id)
    can_proceed = True

    # Verificar besitos de la DECISIÓN
    if decision.required_besitos and decision.required_besitos > 0:
        if user.points < decision.required_besitos:
            requirements_info["missing_besitos"] = decision.required_besitos - user.points
            can_proceed = False

    # Verificar rol de la DECISIÓN
    if decision.required_role:
        user_role = await get_user_role(self.bot, user_id, session=self.session)
        if user_role not in (decision.required_role, "admin"):
            requirements_info["missing_role"] = decision.required_role
            can_proceed = False

    return can_proceed, requirements_info
```

**Archivo**: `services/narrative_service.py`

#### Diferencia Clave

| Aspecto | Antes | Después |
|---------|-------|---------|
| ¿Qué verifica? | Fragmento de destino | Decisión seleccionada |
| Campo besitos | `fragment.min_besitos` | `decision.required_besitos` |
| Campo rol | `fragment.required_role` | `decision.required_role` |
| Retorna | `bool` | `tuple[bool, dict]` |

---

### 2. Mensajes Detallados de Requisitos Bloqueados

#### Funcionalidad Nueva

Cuando un usuario no cumple los requisitos para tomar una decisión, en lugar de mostrar un mensaje genérico, ahora se muestra:

1. **Lista detallada** de requisitos faltantes
2. **Estado actual** vs requerido
3. **Sugerencias** para conseguir lo que falta
4. **Botones de acción** para tienda/VIP

#### Implementación

**Función de visualización** (`handlers/narrative_handler.py`):

```python
async def _show_requirements_message(callback: CallbackQuery, requirements_info: dict, session: AsyncSession):
    """
    Muestra un mensaje detallado de requisitos no cumplidos con opciones de conversión.
    """
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    message_parts = ["🚫 **Contenido Bloqueado**\n\n"]
    message_parts.append("_Esta decisión requiere cumplir ciertos requisitos._\n\n")
    message_parts.append("**📋 Requisitos:**\n")

    # Besitos requirement
    if requirements_info.get("required_besitos", 0) > 0:
        current = requirements_info.get("current_besitos", 0)
        required = requirements_info.get("required_besitos", 0)
        missing = requirements_info.get("missing_besitos", 0)

        status_icon = "✅" if missing <= 0 else "❌"
        message_parts.append(f"{status_icon} **Besitos:** {current:.0f}/{required} ")

        if missing > 0:
            message_parts.append(f"_(Te faltan {missing:.0f})_")
        message_parts.append("\n")

    # Role requirement
    if requirements_info.get("required_role"):
        current_role = requirements_info.get("current_role", "free")
        required_role = requirements_info.get("required_role")
        missing_role = requirements_info.get("missing_role")

        status_icon = "✅" if not missing_role else "❌"
        role_names = {
            "vip": "Membresía VIP",
            "free": "Usuario Gratuito",
            "admin": "Administrador"
        }

        message_parts.append(f"{status_icon} **Acceso:** {role_names.get(current_role)}\n")

        if missing_role:
            message_parts.append(f"_Necesitas: {role_names.get(required_role)}_\n")

    # Add conversion teaser
    message_parts.append("\n💡 **¿Cómo conseguirlo?**\n\n")

    builder = InlineKeyboardBuilder()

    # If missing besitos, offer ways to earn them
    if requirements_info.get("missing_besitos", 0) > 0:
        message_parts.append("💰 **Gana más besitos:**\n")
        message_parts.append("• Completa otros fragmentos de la historia\n")
        message_parts.append("• Participa en eventos y desafíos\n")
        message_parts.append("• Visita la tienda para productos especiales\n\n")

        builder.button(text="🛒 Visitar Tienda", callback_data="shop_access")

    # If missing role (VIP), offer subscription
    if requirements_info.get("missing_role") == "vip":
        message_parts.append("✨ **Hazte VIP:**\n")
        message_parts.append("• Accede a contenido exclusivo\n")
        message_parts.append("• Desbloquea decisiones especiales\n")
        message_parts.append("• Gana el doble de besitos\n\n")

        builder.button(text="👑 Información VIP", callback_data="vip_info")

    builder.button(text="🔙 Volver", callback_data="continue_narrative")
    builder.adjust(1)

    await callback.message.edit_text(
        "".join(message_parts),
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
```

#### Ejemplo de Mensaje

```
🚫 Contenido Bloqueado

Esta decisión requiere cumplir ciertos requisitos.

📋 Requisitos:
❌ Besitos: 25/50 (Te faltan 25)

💡 ¿Cómo conseguirlo?

💰 Gana más besitos:
• Completa otros fragmentos de la historia
• Participa en eventos y desafíos
• Visita la tienda para productos especiales

[🛒 Visitar Tienda]
[🔙 Volver]
```

---

### 3. Otorgamiento de Puntos del Fragmento Inicial

#### Problema

Los usuarios comenzaban con 0 besitos porque el fragmento "start" nunca otorgaba sus puntos iniciales.

**Causa**: El método `get_user_current_fragment()` solo establecía el `current_fragment_key` sin procesar recompensas.

#### Solución

```python
# ✅ DESPUÉS (narrative_service.py)
async def get_user_current_fragment(self, user_id: int) -> Optional[StoryFragment]:
    """Obtiene el fragmento actual del usuario o inicia la narrativa."""
    user_state = await self._get_or_create_user_state(user_id)

    if not user_state.current_fragment_key:
        start_fragment = await self._get_fragment_by_key("start")
        if start_fragment:
            user_state.current_fragment_key = start_fragment.key
            user_state.narrative_started_at = datetime.utcnow()
            user_state.fragments_visited = 1  # ✅ Inicializar contador

            # ✅ Otorgar recompensas del fragmento inicial
            await self._process_fragment_rewards(user_id, start_fragment)

            await self.session.commit()
            logger.info(f"User {user_id} started narrative at 'start' and received {start_fragment.reward_besitos} besitos")
            return start_fragment
        else:
            logger.error("No se encontró fragmento inicial 'start'")
            return None

    return await self._get_fragment_by_key(user_state.current_fragment_key)
```

#### Resultado

- ✅ Usuario recibe besitos del fragmento inicial inmediatamente
- ✅ Contador de fragmentos visitados inicia en 1 (en lugar de 0)
- ✅ Estadísticas de progreso muestran "Fragmento 1/X" correctamente

---

### 4. Estadísticas de Progreso en Cabecera

#### Antes vs Después

**Antes**:
```
📍 Fragmento 0/10 • Nivel 1 • 0%
```

**Después**:
```
📍 Fragmento 1/10 • Nivel 1 • 10%
```

#### Cambios

1. `fragments_visited` se inicializa en `1` al comenzar
2. Se incrementa correctamente al avanzar de fragmento
3. El porcentaje se calcula correctamente

**Archivo**: `services/narrative_service.py` líneas 33, 126

---

## Sistema de Onboarding

### Contexto

Nuevo sistema completo de onboarding para usuarios que solicitan unirse al canal gratuito.

### Características

1. **Narrativa coherente** con voz de Lucien (mayordomo) y Diana
2. **Tiempo de espera configurable** (default: 15 minutos)
3. **Engagement durante la espera**: Enlaces a redes sociales
4. **Verificación de estado** en tiempo real
5. **Bienvenida personalizada** al ser aprobado

### Archivos Creados

#### 1. `utils/onboarding_messages.py`

Contiene todos los mensajes del flujo de onboarding:

```python
def get_join_request_message(wait_minutes: int, social_links: dict) -> tuple[str, list]:
    """Mensaje inicial cuando el usuario solicita unirse."""
    # Retorna (mensaje_texto, lista_de_botones)

def get_welcome_approved_message(username: str = None) -> str:
    """Mensaje de bienvenida cuando el usuario es aprobado."""

def get_reminder_follow_socials(wait_remaining: int, social_links: dict) -> tuple[str, list]:
    """Recordatorio para seguir en redes sociales."""

# Configuración de enlaces
DEFAULT_SOCIAL_LINKS = {
    'instagram': 'https://instagram.com/dianakinky',
    'tiktok': 'https://tiktok.com/@dianakinky',
    'twitter': 'https://twitter.com/dianakinky',
    'onlyfans': 'https://onlyfans.com/dianakinky'
}
```

#### 2. `docs/ONBOARDING_FLUJO.md`

Documentación completa del flujo, casos de uso, testing, y métricas.

### Flujo Detallado

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Usuario solicita unirse al canal gratuito                   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Bot registra solicitud en BD (PendingChannelRequest)        │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Bot envía mensaje de Lucien                                 │
│    - Explica tiempo de espera (15 min)                         │
│    - Ofrece enlaces a redes sociales                           │
│    - Botón "🔄 Ver Estado"                                      │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Durante la espera (opcional)                                │
│    Usuario puede presionar "Ver Estado"                        │
│    - Muestra tiempo restante                                   │
│    - Recuerda seguir redes sociales                            │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼ (15 minutos después)
┌─────────────────────────────────────────────────────────────────┐
│ 5. Scheduler procesa solicitud                                 │
│    - Aprueba en Telegram                                       │
│    - Marca como aprobada en BD                                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. Bot envía mensaje dual                                      │
│    - Lucien anuncia aprobación                                 │
│    - Diana da bienvenida personal                              │
│    - Botones: Historia, VIP, Contenido Gratuito               │
└─────────────────────────────────────────────────────────────────┘
```

### Modificaciones en `services/free_channel_service.py`

#### Mensaje de Solicitud (líneas 114-140)

```python
# Notificar al usuario con nuevo sistema de onboarding
wait_minutes = await self.get_wait_time_minutes()

from utils.onboarding_messages import get_join_request_message, DEFAULT_SOCIAL_LINKS
from aiogram.utils.keyboard import InlineKeyboardBuilder

message_text, social_buttons = get_join_request_message(wait_minutes, DEFAULT_SOCIAL_LINKS)

# Construir teclado con redes sociales
builder = InlineKeyboardBuilder()
for button in social_buttons:
    builder.button(text=button['text'], url=button['url'])

builder.button(text="🔄 Ver Estado", callback_data="check_join_status")
builder.adjust(2, 2, 1)

await self.bot.send_message(
    user_id,
    message_text,
    reply_markup=builder.as_markup(),
    parse_mode="Markdown"
)
```

#### Mensaje de Bienvenida (líneas 176-207)

```python
# Obtener username para personalizar
user = await self.session.get(User, request.user_id)
username = user.username if user and user.username else None

from utils.onboarding_messages import get_welcome_approved_message

welcome_message = get_welcome_approved_message(username)

# Construir teclado con opciones iniciales
builder = InlineKeyboardBuilder()
builder.button(text="📖 Comenzar la Historia", callback_data="start_narrative")
builder.button(text="💎 Ver Membresía VIP", callback_data="vip_info")
builder.button(text="🎁 Contenido Gratuito", callback_data="free_gift")
builder.adjust(1)

await self.bot.send_message(
    request.user_id,
    welcome_message,
    reply_markup=builder.as_markup(),
    parse_mode="Markdown"
)
```

### Handler "Ver Estado" (`handlers/channel_access.py`)

```python
@router.callback_query(lambda c: c.data == "check_join_status")
async def check_join_status_handler(callback, session: AsyncSession):
    """Verifica el estado de la solicitud de ingreso al canal gratuito."""

    user_id = callback.from_user.id

    # Buscar solicitud pendiente
    stmt = select(PendingChannelRequest).where(
        PendingChannelRequest.user_id == user_id,
        PendingChannelRequest.approved == False
    )
    result = await session.execute(stmt)
    pending_request = result.scalar_one_or_none()

    if not pending_request:
        await callback.answer("✅ Tu solicitud ya fue aprobada.", show_alert=True)
        return

    # Calcular tiempo restante
    config = await session.get(BotConfig, 1)
    wait_minutes = config.free_channel_wait_time_minutes if config else 15

    elapsed_time = datetime.utcnow() - pending_request.request_timestamp
    elapsed_minutes = int(elapsed_time.total_seconds() / 60)
    remaining_minutes = max(0, wait_minutes - elapsed_minutes)

    # Mensaje según tiempo restante
    if remaining_minutes == 0:
        status_message = "⏰ Tu solicitud está siendo procesada..."
    elif remaining_minutes < 5:
        status_message = f"⏰ **¡Casi listo!**\n\nTiempo restante: ~{remaining_minutes} min"
    else:
        status_message = f"""⏰ **Estado de tu Solicitud**

Tiempo transcurrido: {elapsed_minutes} minutos
Tiempo restante: **{remaining_minutes} minutos**

_Recuerda: seguir a Diana demuestra tu interés genuino._"""

    # Actualizar mensaje con estado
    builder = InlineKeyboardBuilder()
    builder.button(text="📸 Instagram", url=DEFAULT_SOCIAL_LINKS['instagram'])
    builder.button(text="🎵 TikTok", url=DEFAULT_SOCIAL_LINKS['tiktok'])
    builder.button(text="🔄 Actualizar Estado", callback_data="check_join_status")
    builder.adjust(2, 1)

    await callback.message.edit_text(
        status_message,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
```

---

## Scheduler de Suscripciones VIP

### Problema: Suscripciones VIP sin Fecha de Expiración

#### Contexto

El scheduler `run_vip_membership_check()` creaba suscripciones VIP permanentes (`expires_at=None`) para usuarios que estaban en el canal VIP pero no tenían registro en la base de datos.

**Código original** (`services/scheduler.py:114`):

```python
# ❌ ANTES
if member.status in {"member", "administrator", "creator"}:
    user.role = "vip"
    sub_service = SubscriptionService(session)
    sub = await sub_service.get_subscription(user.id)
    if not sub:
        await sub_service.create_subscription(user.id, None)  # ❌ Suscripción permanente
```

#### Problema

1. Usuarios podían entrar al canal VIP manualmente (sin token)
2. El sistema les creaba una suscripción permanente
3. No había validación de tokens o pagos

#### Solución

Modificado para **remover** usuarios sin suscripción válida en lugar de crearles una:

```python
# ✅ DESPUÉS
async def run_vip_membership_check(bot: Bot, session_factory: async_sessionmaker[AsyncSession]):
    """Ensure users in the VIP channel have valid subscriptions, remove those without."""
    async with session_factory() as session:
        vip_channel_id = await ConfigService(session).get_vip_channel_id()
        if not vip_channel_id:
            return

        stmt = select(User).where(User.role != "vip")
        result = await session.execute(stmt)
        users = result.scalars().all()

        updated = 0
        removed = 0

        for user in users:
            try:
                member = await bot.get_chat_member(vip_channel_id, user.id)
                if member.status in {"member", "administrator", "creator"}:
                    sub_service = SubscriptionService(session)
                    sub = await sub_service.get_subscription(user.id)

                    # ✅ Solo sincronizar si tienen suscripción VÁLIDA
                    if sub and await sub_service.is_subscription_active(user.id):
                        user.role = "vip"
                        updated += 1
                        logging.info(f"Synced user {user.id} to VIP (has valid subscription)")
                    else:
                        # ✅ Remover del canal si no tienen suscripción válida
                        try:
                            await bot.ban_chat_member(vip_channel_id, user.id)
                            await bot.unban_chat_member(vip_channel_id, user.id)
                            removed += 1
                            logging.info(f"Removed user {user.id} from VIP (no valid subscription)")
                        except Exception as kick_error:
                            logging.warning(f"Could not remove user {user.id}: {kick_error}")
            except Exception as e:
                logging.debug(f"Error checking user {user.id}: {e}")
                continue

        if updated or removed:
            await session.commit()
            logging.info(f"VIP membership check: synced {updated}, removed {removed}")
```

#### Flujo Correcto Ahora

```
1. Usuario activa token VIP
   ↓
2. Se crea suscripción en BD con expires_at
   ↓
3. Usuario es invitado al canal VIP
   ↓
4. Scheduler verifica periódicamente:
   - ✅ Tiene suscripción válida? → Mantener en canal
   - ❌ No tiene suscripción? → Remover del canal
   ↓
5. Cuando expira suscripción:
   - BD: expires_at < now
   - Scheduler lo detecta y lo remueve del canal
```

**Archivo**: `services/scheduler.py` líneas 96-138

---

## Archivos Modificados

### Archivos Principales

| Archivo | Cambios | Líneas |
|---------|---------|--------|
| `handlers/admin/event_admin.py` | Agregado parámetro `session` a 6 funciones | 66-189 |
| `utils/messages.py` | Agregadas 11 claves a `BOT_MESSAGES` | 174-184 |
| `handlers/main_menu.py` | Modificado `return_to_main_menu()` para usar `MenuFactory` | 138-166 |
| `services/narrative_service.py` | • Nuevo método `_check_decision_requirements()`<br>• Otorgamiento de puntos iniciales<br>• Método `check_decision_requirements_info()` | 24-45, 217-272 |
| `handlers/narrative_handler.py` | • Nueva función `_show_requirements_message()`<br>• Handler actualizado para requisitos | 238-244, 1209-1313 |
| `services/scheduler.py` | Modificado `run_vip_membership_check()` | 96-138 |
| `services/free_channel_service.py` | • Integración de onboarding messages<br>• Mensajes de bienvenida mejorados | 114-207 |
| `handlers/channel_access.py` | Agregado handler `check_join_status_handler()` | 116-184 |

### Archivos Nuevos

| Archivo | Propósito |
|---------|-----------|
| `utils/onboarding_messages.py` | Mensajes de onboarding con voz de Lucien/Diana |
| `docs/ONBOARDING_FLUJO.md` | Documentación completa del flujo de onboarding |
| `docs/SESSION_2025-10-01_MENU_SYSTEM_UPDATES.md` | Este documento |

---

## Testing

### Tests Realizados

#### 1. Sistema de Menús
- ✅ Usuario gratuito ve menú gratuito al regresar de narrativa
- ✅ Usuario VIP ve menú VIP al regresar de narrativa
- ✅ Admin ve panel de administración

#### 2. Sistema de Narrativa
- ✅ Fragmento inicial otorga puntos correctamente
- ✅ Estadísticas muestran "Fragmento 1/X" desde el inicio
- ✅ Decisiones con requisitos se validan correctamente
- ✅ Mensaje detallado se muestra cuando faltan requisitos
- ✅ Botones de conversión (tienda/VIP) funcionan

#### 3. Scheduler VIP
- ✅ Usuarios sin suscripción son removidos del canal VIP
- ✅ Usuarios con suscripción válida se mantienen
- ✅ No se crean más suscripciones sin `expires_at`

### Tests Pendientes

```python
# TODO: Implementar tests unitarios
# - test_menu_factory_returns_correct_menu_for_role()
# - test_narrative_initial_fragment_awards_points()
# - test_decision_requirements_validation()
# - test_requirements_message_generation()
# - test_vip_scheduler_removes_invalid_users()
# - test_onboarding_flow_complete()
```

### Cómo Probar Onboarding

1. **Reducir tiempo de espera a 1 minuto**:
   ```bash
   # Panel Admin → Canal Gratuito → Configurar: 1 minuto
   ```

2. **Crear cuenta de prueba**:
   - Usar otro número/cuenta de Telegram
   - Solicitar unirse al canal gratuito

3. **Verificar**:
   - ✅ Mensaje de Lucien con enlaces sociales
   - ✅ Botón "Ver Estado" funciona y muestra tiempo
   - ✅ Aprobación automática después de 1 minuto
   - ✅ Mensaje dual (Lucien + Diana)
   - ✅ Botones de inicio funcionan

4. **Restaurar configuración**:
   ```bash
   # Panel Admin → Canal Gratuito → Configurar: 15 minutos
   ```

---

## Mejoras Futuras

### Sistema de Menús
- [ ] Caché de menús para mejorar performance
- [ ] Menús contextuales según estado narrativo
- [ ] A/B testing de diferentes layouts

### Sistema de Narrativa
- [ ] Analytics de decisiones más tomadas/rechazadas
- [ ] Sistema de hints para requisitos faltantes
- [ ] Previsualizaciones de fragmentos bloqueados

### Sistema de Onboarding
- [ ] Verificación automática de follows en redes sociales
- [ ] Reducción de tiempo de espera si sigue en Instagram/TikTok
- [ ] Mini-quiz durante la espera para ganar besitos
- [ ] Segmentación de mensajes según origen del tráfico

### Scheduler
- [ ] Dashboard de métricas del scheduler
- [ ] Alertas cuando hay muchos usuarios removidos
- [ ] Logs estructurados para análisis

---

## Conclusión

Esta sesión se enfocó en:

1. **Estabilidad**: Corrección de bugs críticos (session, BOT_MESSAGES)
2. **UX**: Menús contextuales según rol de usuario
3. **Engagement**: Sistema de requisitos con mensajes de conversión
4. **Onboarding**: Flujo completo con narrativa coherente
5. **Seguridad**: Prevención de suscripciones VIP no autorizadas

**Resultado**: Sistema más robusto, coherente y orientado a conversión.

---

## Referencias

- [Documentación de Onboarding](/docs/ONBOARDING_FLUJO.md)
- [Código de Menús](/utils/menu_factory.py)
- [Código de Narrativa](/services/narrative_service.py)
- [Código de Scheduler](/services/scheduler.py)

---

**Última actualización**: 2025-10-01
**Autor**: Claude Code
**Versión**: 1.0
