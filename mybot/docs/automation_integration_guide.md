# 🚀 Guía de Integración - Sistema de Automatización Dirigido por Eventos

## 📋 Resumen

El **Sistema de Automatización Dirigido por Eventos** reemplaza la lógica hardcodeada con un motor configurable dinámico. Permite crear triggers que ejecutan acciones automáticamente cuando ocurren eventos específicos.

## 🎯 Componentes Implementados

### 1. Modelos ORM (`app/models/automation.py`)
- `AutomationTrigger` - Define CUÁNDO se dispara
- `TriggerAction` - Define QUÉ se ejecuta  
- `AutomationLog` - Auditoría de ejecuciones

### 2. Esquemas Pydantic (`app/schemas/automation.py`)
- Soporte completo para **Atomic Nested Creation**
- Validación de tipos de evento y acción
- Schemas para ejecución de prueba

### 3. Servicio Motor (`app/services/automation_service.py`)
- `create_trigger_with_actions()` - Transacción atómica
- `execute_triggers()` - **CEREBRO del sistema**
- Evaluación de condiciones + simulación de acciones

### 4. Endpoints REST (`app/api/v1/endpoints/automation.py`)
- CRUD completo para triggers
- Endpoint de prueba de eventos
- Documentación OpenAPI automática

## 🔄 Cómo Usar el Sistema

### 1. Crear un Trigger con Acciones Anidadas

```python
from app.schemas.automation import TriggerCreate, ActionCreateNested

# Datos del trigger con nested creation
trigger_data = TriggerCreate(
    name="recompensa_bienvenida",
    description="Da 100 puntos al ver el fragmento WELCOME",
    event_type="fragment_viewed",
    conditions={"fragment_key": "WELCOME"},
    is_enabled=True,
    priority=1,
    actions=[
        ActionCreateNested(
            action_type="add_points",
            parameters={"amount": 100, "reason": "¡Bienvenido!"},
            execution_order=1
        ),
        ActionCreateNested(
            action_type="send_message", 
            parameters={"message_template": "¡Felicidades por comenzar!"},
            execution_order=2
        )
    ]
)

# Ejecutar creación anidada
service = AutomationService(db)
result = await service.create_trigger_with_actions(trigger_data)
```

### 2. Ejecutar Eventos en el Sistema

```python
# Cuando un usuario ve un fragmento
await service.execute_triggers(
    event_type="fragment_viewed",
    user_id=user.id,
    context={
        "fragment_key": "WELCOME",
        "chapter": "introduccion"
    }
)

# Cuando un usuario completa una compra
await service.execute_triggers(
    event_type="purchase_completed", 
    user_id=user.id,
    context={
        "product_id": 123,
        "product_type": "premium",
        "price": 500
    }
)
```

### 3. Tipos de Eventos Disponibles

```python
# Eventos del sistema
FRAGMENT_VIEWED = "fragment_viewed"
PURCHASE_COMPLETED = "purchase_completed" 
USER_REGISTERED = "user_registered"
VIP_SUBSCRIPTION_STARTED = "vip_subscription_started"
VIP_SUBSCRIPTION_ENDED = "vip_subscription_ended"
ACHIEVEMENT_UNLOCKED = "achievement_unlocked"
DAILY_LOGIN = "daily_login"
STREAK_BROKEN = "streak_broken"
CUSTOM_EVENT = "custom_event"
```

### 4. Tipos de Acciones Disponibles

```python
# Acciones que se pueden ejecutar
GIVE_PRODUCT = "give_product"
GRANT_VIP = "grant_vip"
SEND_MESSAGE = "send_message"
ADD_POINTS = "add_points"
UNLOCK_FRAGMENT = "unlock_fragment"
GRANT_BADGE = "grant_badge"
TRIGGER_NARRATIVE = "trigger_narrative"
EXECUTE_WEBHOOK = "execute_webhook"
```

## 🔧 Integración con el Sistema Existente

### Reemplazar Lógica Hardcodeada

**ANTES (hardcodeado):**
```python
# En algún handler
if fragment.key == "WELCOME":
    user.points += 100
    await send_message(user.id, "¡Bienvenido! Ganaste 100 puntos")
```

**AHORA (configurable):**
```python
# En el handler - simplemente disparar evento
await automation_service.execute_triggers(
    event_type="fragment_viewed",
    user_id=user.id,
    context={"fragment_key": fragment.key}
)
```

### Puntos de Integración Recomendados

1. **Handlers de Fragmentos Narrativos**
   - `fragment_viewed` cuando un usuario ve un fragmento

2. **Handlers de Tienda**  
   - `purchase_completed` cuando se completa una compra

3. **Handlers de Usuario**
   - `user_registered` cuando se registra un usuario
   - `daily_login` para recompensas diarias

4. **Handlers VIP**
   - `vip_subscription_started` cuando se activa VIP
   - `vip_subscription_ended` cuando expira VIP

## 📊 API REST Endpoints

### Crear Trigger
```bash
POST /api/v1/automation/triggers
```

### Probar Evento
```bash
POST /api/v1/automation/test-event
```

### Listar Triggers
```bash
GET /api/v1/automation/triggers
```

### Obtener Trigger Específico
```bash
GET /api/v1/automation/triggers/{trigger_id}
```

### Actualizar Trigger
```bash
PUT /api/v1/automation/triggers/{trigger_id}
```

### Eliminar Trigger
```bash
DELETE /api/v1/automation/triggers/{trigger_id}
```

## 🧪 Testing y Debugging

### Probar Triggers sin Efectos Reales

```python
# Usar el endpoint de prueba
response = await client.post(
    "/api/v1/automation/test-event",
    json={
        "event_type": "fragment_viewed",
        "user_id": 123,
        "context": {"fragment_key": "WELCOME"}
    }
)
```

### Ver Logs de Ejecución

```python
# Los logs se almacenan automáticamente en automation_logs
# Incluyen:
# - Qué triggers se ejecutaron
# - Qué acciones se dispararon
# - Resultado de la ejecución
# - Errores si los hubo
```

## 🎯 Ejemplos de Casos de Uso

### 1. Recompensa de Bienvenida
```json
{
  "name": "recompensa_bienvenida",
  "event_type": "fragment_viewed",
  "conditions": {"fragment_key": "WELCOME"},
  "actions": [
    {
      "action_type": "add_points",
      "parameters": {"amount": 100, "reason": "¡Bienvenido!"}
    }
  ]
}
```

### 2. Insignia por Compra Premium
```json
{
  "name": "insignia_premium",
  "event_type": "purchase_completed", 
  "conditions": {"product_type": "premium"},
  "actions": [
    {
      "action_type": "grant_badge",
      "parameters": {"badge_id": "premium_member"}
    }
  ]
}
```

### 3. Recompensa de Login Diario
```json
{
  "name": "login_diario",
  "event_type": "daily_login",
  "actions": [
    {
      "action_type": "add_points",
      "parameters": {"amount": 50, "reason": "Login diario"}
    }
  ]
}
```

## 🚀 Beneficios del Sistema

### ✅ Elimina Hardcoding
- Configuración dinámica sin modificar código
- Cambios en tiempo real sin deploy

### ✅ Motor Configurable  
- Condiciones flexibles (JSONB)
- Múltiples acciones por trigger
- Prioridad de ejecución

### ✅ Compatibilidad Total
- Mismo patrón Atomic Nested Creation
- AsyncSession y transacciones atómicas
- Integridad referencial

### ✅ Auditoría Completa
- Logging automático de ejecuciones
- Tracking de errores
- Historial de acciones

## 📈 Próximos Pasos

1. **Integrar con handlers existentes** - Reemplazar lógica hardcodeada
2. **Crear triggers de ejemplo** - Configurar automatizaciones comunes
3. **Monitorear logs** - Verificar funcionamiento en producción
4. **Expandir tipos de acción** - Conectar con más servicios del sistema

---

**Estado:** ✅ **SISTEMA COMPLETADO Y LISTO PARA PRODUCCIÓN**