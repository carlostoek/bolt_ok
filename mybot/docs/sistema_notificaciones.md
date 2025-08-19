# Sistema de Notificaciones Unificadas

## Descripción General

El sistema de notificaciones unificadas proporciona una manera centralizada y consistente de enviar mensajes a los usuarios. Está diseñado para:

1. **Agregar notificaciones relacionadas** en un solo mensaje
2. **Priorizar notificaciones** según su importancia
3. **Evitar duplicados** mediante detección de hashes
4. **Formatear mensajes** con una personalidad y estilo coherentes
5. **Gestionar tiempos de espera** para optimizar la experiencia del usuario

## Arquitectura

### Componentes Principales

1. **NotificationService**
   - Servicio centralizado para el manejo de notificaciones
   - Mantiene colas de notificaciones pendientes por usuario
   - Programa el envío con retrasos inteligentes

2. **NotificationPriority**
   - Enumerador de prioridades: CRITICAL, HIGH, MEDIUM, LOW
   - Determina los tiempos de agregación y urgencia

3. **NotificationData**
   - Estructura de datos para cada notificación
   - Contiene tipo, datos específicos, prioridad y timestamp
   - Genera hashes para detección de duplicados

4. **CoordinadorCentral**
   - Orquesta el flujo de notificaciones desde diferentes subsistemas
   - Método `_send_unified_notifications` para procesamiento centralizado

## Flujo de Trabajo

1. Una acción del usuario (reacción, completar misión, etc.) ocurre
2. El handler llama al método correspondiente del CoordinadorCentral
3. El CoordinadorCentral procesa la acción y genera resultados
4. Se crea un NotificationService y se añaden notificaciones mediante `add_notification()`
5. Las notificaciones se programan para envío con un retraso basado en su prioridad
6. Después del retraso, las notificaciones se combinan en un mensaje coherente
7. El mensaje se envía al usuario

## Tipos de Notificaciones

1. **points**: Notificaciones de puntos ganados
   - Prioridad: LOW (por defecto) o MEDIUM (cantidades grandes)
   - Datos: `{"points": float, "total": float}`

2. **mission**: Notificaciones de misiones completadas
   - Prioridad: MEDIUM o HIGH (misiones importantes)
   - Datos: `{"name": str, "points": float, "description": str}`

3. **achievement**: Notificaciones de logros
   - Prioridad: HIGH
   - Datos: `{"name": str, "description": str, "icon": str}`

4. **reaction**: Notificaciones de reacciones
   - Prioridad: LOW
   - Datos: `{"type": str, "reaction_type": str}`

5. **level**: Notificaciones de subida de nivel
   - Prioridad: HIGH
   - Datos: `{"level": int, "name": str, "points_needed": int}`

## Integración con Servicios Existentes

### Servicio de Misiones

El servicio de misiones utiliza el sistema de notificaciones en dos lugares clave:

1. **complete_mission()**: Al completar una misión directamente
   - Usa `skip_notification=True` en `add_points()` para evitar duplicados
   - Añade una notificación de tipo "mission" al sistema unificado

2. **update_progress()**: Al actualizar el progreso incremental
   - Cuando se completa una misión, añade una notificación
   - Usa `bot=None` para evitar envíos directos

### Servicio de Puntos

El servicio de puntos se integra mediante:

1. **add_points()**: Acepta un parámetro `skip_notification`
   - Si es `False`, envía notificación solo cuando hay un cambio significativo
   - Intenta usar el sistema unificado, con fallback al sistema anterior

2. **award_message()**, **award_reaction()**, etc.: Métodos que otorgan puntos
   - Ahora utilizan `skip_notification=True` para delegar al sistema unificado

### Handlers de Reacciones

Los handlers de reacciones ahora:

1. **Muestran solo notificaciones emergentes**: Para feedback inmediato
2. **No envían mensajes duplicados**: Evitan llamadas redundantes a `bot.send_message()`
3. **Delegan al sistema unificado**: Para mensajes consistentes

## Problemas Resueltos

1. **Notificaciones duplicadas**: Se enviaban mensajes desde múltiples lugares
   - Ahora hay un único punto de salida para notificaciones
   - Se controla con `skip_notification` y `bot=None`

2. **Inconsistencia en mensajes**: Formatos diferentes según el origen
   - Ahora todos los mensajes pasan por el mismo formateador

3. **Sobrecarga de mensajes**: Demasiadas notificaciones individuales
   - Las notificaciones se agrupan por tipo y tiempo

## Guía de Uso

### Cómo Añadir Notificaciones

```python
# 1. Importar el servicio
from services.notification_service import NotificationService, NotificationPriority

# 2. Crear una instancia
notification_service = NotificationService(session, bot)

# 3. Añadir una notificación
await notification_service.add_notification(
    user_id,
    "tipo_notificacion",  # Ej: "points", "mission", "achievement"
    {
        # Datos específicos del tipo
        "key1": "valor1",
        "key2": "valor2",
    },
    priority=NotificationPriority.MEDIUM  # Opcional, MEDIUM por defecto
)
```

### Cuando se Otorgan Puntos

```python
# Evitar duplicación en notificaciones
await point_service.add_points(user_id, points, bot=bot, skip_notification=True)

# Luego añadir la notificación al sistema unificado
await notification_service.add_notification(
    user_id,
    "points",
    {"points": points, "total": total_points},
    priority=NotificationPriority.LOW
)
```

### En Acciones de Usuario

Para manejar acciones del usuario, use el CoordinadorCentral:

```python
coordinador = CoordinadorCentral(session)
result = await coordinador.ejecutar_flujo(
    user_id,
    AccionUsuario.TIPO_ACCION,  # Ej: REACCIONAR_PUBLICACION_NATIVA
    # Parámetros adicionales según la acción
    bot=bot
)
```

El CoordinadorCentral se encargará de las notificaciones automáticamente.

## Mejores Prácticas

1. **No enviar notificaciones duplicadas**:
   - Usar `skip_notification=True` o `bot=None` cuando se delega al sistema unificado
   - No llamar a `bot.send_message()` para confirmaciones que el sistema unificado ya maneja

2. **Respetar las prioridades**:
   - CRITICAL: Solo para errores o información crítica (0.1s de delay)
   - HIGH: Logros, niveles, misiones importantes (0.5s)
   - MEDIUM: Misiones normales, cantidades significativas de puntos (1.0s)
   - LOW: Reacciones, pequeñas cantidades de puntos (1.5s)

3. **Estructurar datos consistentemente**:
   - Seguir los formatos establecidos para cada tipo de notificación
   - Incluir todos los campos esperados

4. **Usar el flush cuando sea necesario**:
   - Para envíos inmediatos: `await notification_service.flush_pending_notifications(user_id)`

## Configuración

El sistema se puede configurar modificando:

- **Tiempos de agregación**: Por prioridad, en segundos
- **Tamaño máximo de cola**: Fuerza envío cuando se alcanza
- **Detección de duplicados**: Ventana de tiempo para considerar duplicados
- **Formato de mensajes**: Opciones de personalización del aspecto