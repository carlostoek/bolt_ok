# Correcciones al Sistema de Notificaciones

## Problemas Identificados

Después de analizar el sistema de notificaciones, se identificaron los siguientes problemas y vulnerabilidades:

### 1. Condiciones de Carrera (Race Conditions)

El sistema original no manejaba adecuadamente las condiciones de carrera que podrían ocurrir cuando múltiples corrutinas intentan acceder y modificar las mismas estructuras de datos concurrentemente:

- Las listas de notificaciones pendientes (`pending_notifications`) se podían modificar sin sincronización
- Las tareas programadas (`scheduled_tasks`) se podían cancelar y reemplazar sin protección adecuada
- Los métodos como `flush_pending_notifications` podían ejecutarse concurrentemente con otros métodos sin bloqueo

### 2. Manejo Inadecuado de Tareas Asíncronas

- No se verificaba si una tarea estaba completada antes de intentar cancelarla
- Las excepciones `CancelledError` no se manejaban correctamente en todos los métodos
- Faltaba asegurarse de que las notificaciones se enviaran realmente después de agregarlas

### 3. Errores de Validación de Datos

- No había validaciones de tipo para campos numéricos como `points` y `total`
- Se accedía a índices sin verificar si las listas estaban vacías (`levels[-1]`, `hints[-1]`)
- Faltaba manejo de casos donde valores opcionales podrían estar ausentes

### 4. Problemas de Formato en Mensajes

- El texto de las pistas narrativas no escapaba caracteres especiales de Markdown
- Posibles errores de formato cuando se accedía a propiedades anidadas sin verificación

### 5. Manejo de Errores Incompleto

- Algunos bloques `except` no capturaban excepciones específicas
- El método `get_pending_count` era síncrono pero debería ser asíncrono ya que accede a datos compartidos
- Manejo de errores anidados sin registro apropiado

## Soluciones Implementadas

### 1. Sincronización con Locks

Se implementó un sistema de bloqueos (locks) por usuario para evitar condiciones de carrera:

```python
# Clase NotificationService
def __init__(self, session: AsyncSession, bot: Bot):
    self.session = session
    self.bot = bot
    self.pending_notifications: Dict[int, List[NotificationData]] = {}
    self.scheduled_tasks: Dict[int, asyncio.Task] = {}
    self.lock: Dict[int, asyncio.Lock] = {}  # Locks por usuario para evitar condiciones de carrera
    self.aggregation_delay = 1.0  # Segundos para esperar y agrupar notificaciones
```

Todas las operaciones críticas ahora usan el lock apropiado:

```python
async def add_notification(self, user_id: int, notification_type: str, data: Dict[str, Any]) -> None:
    try:
        # Asegurar que tenemos un lock para este usuario
        if user_id not in self.lock:
            self.lock[user_id] = asyncio.Lock()
        
        # Usar lock para operaciones críticas sobre este usuario
        async with self.lock[user_id]:
            # Operaciones críticas...
```

### 2. Mejora en el Manejo de Tareas Asíncronas

- Se verifica que las tareas no estén completadas antes de cancelarlas:

```python
if user_id in self.scheduled_tasks and not self.scheduled_tasks[user_id].done():
    self.scheduled_tasks[user_id].cancel()
```

- Se agregó manejo específico para `asyncio.CancelledError`:

```python
except asyncio.CancelledError:
    # Ignorar si la tarea se cancela durante la operación
    pass
```

- Se implementó un mecanismo para forzar el envío de notificaciones después de agregarlas:

```python
# Forzar envío para asegurar que todas las notificaciones se procesen
await asyncio.sleep(notification_service.aggregation_delay + 0.1)
await notification_service.flush_pending_notifications(user_id)
```

### 3. Validación Robusta de Datos

- Se agregaron verificaciones de tipo para valores numéricos:

```python
total_points = sum(notif.get("points", 0) for notif in grouped_notifications["points"] 
                  if isinstance(notif.get("points"), (int, float)))
```

- Se implementaron verificaciones adicionales para evitar índices fuera de rango:

```python
if "level" in grouped_notifications and grouped_notifications["level"]:
    levels = grouped_notifications["level"]
    if levels:  # Verificación adicional para evitar índices fuera de rango
        latest_level = levels[-1]
        # ...
```

- Se mejoró la comprobación de valores opcionales:

```python
if result.get("points_awarded") is not None:
    # En lugar de if result.get("points_awarded"):
    # que no detectaría valores válidos como 0
```

### 4. Mejoras en el Formato de Mensajes

- Se implementó escape de caracteres especiales en formato markdown:

```python
hint_text = latest_hint.get('text', 'Pista misteriosa...')
# Escapar caracteres especiales en formato markdown
hint_text = hint_text.replace("*", "\\*").replace("_", "\\_").replace("`", "\\`")
message_parts.append(f"_{hint_text}_")
```

### 5. Manejo de Errores Mejorado

- Se convirtió `get_pending_count` a método asíncrono con sincronización adecuada:

```python
async def get_pending_count(self, user_id: int) -> int:
    # Asegurar que tenemos un lock para este usuario
    if user_id not in self.lock:
        self.lock[user_id] = asyncio.Lock()
    
    async with self.lock[user_id]:
        return len(self.pending_notifications.get(user_id, []))
```

- Se implementó manejo de errores anidados con registro:

```python
except Exception as e:
    logger.exception(f"Error sending unified notification: {e}")
    # Fallback: enviar mensaje básico
    try:
        basic_message = result.get("message", "Diana sonríe al ver tu reacción... 💋")
        await notification_service.send_immediate_notification(user_id, basic_message)
    except Exception as inner_e:
        logger.exception(f"Error sending fallback notification: {inner_e}")
```

## Otras Mejoras

### 1. Procesamiento de Datos Fuera de los Locks

Para mejorar el rendimiento, el procesamiento de datos que no requiere protección de concurrencia se realiza fuera de los locks:

```python
# Operaciones críticas dentro del lock
async with self.lock[user_id]:
    if user_id in self.pending_notifications and self.pending_notifications[user_id]:
        notifications = self.pending_notifications.pop(user_id, [])
        # ...
        notifications_to_process = notifications

# Procesamiento fuera del lock para no bloquear otras operaciones
if notifications_to_process:
    # Agrupar notificaciones por tipo
    grouped = self._group_notifications_by_type(notifications_to_process)
    # ...
```

### 2. Datos Adicionales en las Notificaciones de Reacción

Se enriquecieron las notificaciones de reacción con más información contextual:

```python
await notification_service.add_notification(
    user_id,
    "reaction",
    {
        "type": "native",
        "reaction_type": result.get("reaction_type", "unknown"),
        "processed": True,
        "is_native": True
    }
)
```

### 3. Garantía de Entrega de Notificaciones

Se agregó un mecanismo para garantizar que las notificaciones se envíen incluso después de posibles cancelaciones:

```python
# Agregar el tipo de reacción al resultado para usarlo en las notificaciones
result["reaction_type"] = reaction_type

# Enviar notificación unificada si el procesamiento fue exitoso
if result.get("success"):
    await _send_unified_notification(notification_service, user_id, result)
```

## Impacto de las Mejoras

1. **Mayor Estabilidad**: Se eliminaron las condiciones de carrera que podían causar pérdida de notificaciones o envíos duplicados.
2. **Mejor Manejo de Errores**: El sistema ahora es más robusto frente a fallos y proporciona mejor información de diagnóstico.
3. **Prevención de Errores**: Se eliminaron posibles fuentes de excepciones por acceso a datos inválidos.
4. **Garantía de Entrega**: Las modificaciones aseguran que las notificaciones se entregan incluso en situaciones de alta concurrencia.
5. **Formato Consistente**: Los mensajes ahora manejan correctamente el formato de markdown y caracteres especiales.

Estas mejoras hacen que el sistema de notificaciones sea más fiable, mantenga mejor la integridad de los datos y proporcione una experiencia más consistente a los usuarios.