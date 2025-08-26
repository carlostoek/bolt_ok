# Guía de Troubleshooting - Sistema de Interfaces

## Introducción

Esta guía proporciona soluciones sistemáticas para problemas comunes en el sistema de interfaces del bot Diana. Los problemas están organizados por categoría con diagnósticos paso a paso y soluciones probadas.

## Tabla de Contenidos

1. [Problemas de Estados Emocionales](#problemas-de-estados-emocionales)
2. [Problemas de Content Delivery](#problemas-de-content-delivery)
3. [Problemas de Procesamiento de Interacciones](#problemas-de-procesamiento-de-interacciones)
4. [Problemas del EventBus](#problemas-del-eventbus)
5. [Problemas de Integración CoordinadorCentral](#problemas-de-integración-coordinadorcentral)
6. [Problemas de Performance](#problemas-de-performance)
7. [Problemas de Base de Datos](#problemas-de-base-de-datos)
8. [Herramientas de Debugging](#herramientas-de-debugging)

## Problemas de Estados Emocionales

### Problema 1: Estado emocional no se actualiza

**Síntomas:**
- Usuario reporta que el bot no responde a su estado de ánimo
- Los logs muestran que `analyze_interaction_emotion()` retorna siempre `NEUTRAL`
- El tono del contenido no cambia

**Diagnóstico:**
```python
# 1. Verificar si el servicio de estados emocionales está funcionando
coordinator = CoordinadorCentral(session)
try:
    current_state = await coordinator.emotional_state_service.get_user_emotional_state(user_id)
    print(f"Estado actual: {current_state.primary_state.value}")
    print(f"Intensidad: {current_state.intensity}")
    print(f"Última actualización: {current_state.last_updated}")
except Exception as e:
    print(f"Error obteniendo estado: {e}")

# 2. Verificar análisis de interacciones
test_interaction = {
    "type": "fragment_completion",
    "completion_time": 25,
    "user_choice": "positive"
}
try:
    inferred_state = await coordinator.emotional_state_service.analyze_interaction_emotion(
        user_id, test_interaction
    )
    print(f"Estado inferido: {inferred_state.value}")
except Exception as e:
    print(f"Error en análisis: {e}")
```

**Soluciones:**

1. **Problema con la base de datos:**
```python
# Verificar que el usuario existe en la tabla de estados emocionales
async def fix_missing_emotional_state(user_id: int):
    coordinator = CoordinadorCentral(session)
    
    try:
        # Forzar creación de estado por defecto
        await coordinator.emotional_state_service._create_default_emotional_state(user_id)
        print(f"Estado emocional creado para usuario {user_id}")
    except Exception as e:
        print(f"Error creando estado: {e}")
```

2. **Problema con lógica de análisis:**
```python
# Verificar que los datos de interacción tienen el formato correcto
def validate_interaction_data(interaction_data: Dict[str, Any]) -> bool:
    required_fields = ["type"]
    
    if not all(field in interaction_data for field in required_fields):
        print(f"Missing required fields. Required: {required_fields}")
        print(f"Received: {list(interaction_data.keys())}")
        return False
    
    valid_types = ["fragment_completion", "choice_selection", "failed_attempt", 
                   "poll_answer", "reaction", "message", "command"]
    
    if interaction_data["type"] not in valid_types:
        print(f"Invalid interaction type: {interaction_data['type']}")
        print(f"Valid types: {valid_types}")
        return False
    
    return True
```

3. **Reset manual del estado emocional:**
```python
async def reset_emotional_state(user_id: int):
    coordinator = CoordinadorCentral(session)
    
    await coordinator.emotional_state_service.update_emotional_state(
        user_id,
        EmotionalState.NEUTRAL,
        0.5,
        "manual_reset_troubleshooting"
    )
    print(f"Estado emocional reseteado para usuario {user_id}")
```

### Problema 2: Estados emocionales inconsistentes

**Síntomas:**
- Estados emocionales cambian erraticamente
- Intensidad fuera del rango 0.0-1.0
- Errores de validación en `EmotionalContext`

**Diagnóstico:**
```python
async def diagnose_emotional_consistency(user_id: int):
    coordinator = CoordinadorCentral(session)
    
    # Obtener estado actual
    context = await coordinator.emotional_state_service.get_user_emotional_state(user_id)
    
    # Validar consistencia
    issues = []
    
    if not 0.0 <= context.intensity <= 1.0:
        issues.append(f"Intensidad inválida: {context.intensity}")
    
    if context.last_updated > datetime.now():
        issues.append(f"Fecha futura: {context.last_updated}")
    
    for state, intensity in context.secondary_states.items():
        if not 0.0 <= intensity <= 1.0:
            issues.append(f"Intensidad secundaria inválida: {state.value}={intensity}")
    
    if issues:
        print("Inconsistencias encontradas:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    
    print("Estado emocional consistente")
    return True
```

**Solución:**
```python
async def repair_emotional_state(user_id: int):
    from docs.escenarios_integracion_avanzados import handle_corrupted_emotional_state
    
    coordinator = CoordinadorCentral(session)
    result = await handle_corrupted_emotional_state(coordinator, user_id)
    
    if result["success"]:
        print(f"Estado reparado: {result['action']}")
    else:
        print(f"Error en reparación: {result['error']}")
```

## Problemas de Content Delivery

### Problema 3: Contenido no se personaliza

**Síntomas:**
- Variables como `{user_name}` aparecen sin reemplazar
- El tono emocional no se refleja en el contenido
- Contenido genérico en lugar de personalizado

**Diagnóstico:**
```python
async def test_content_personalization():
    coordinator = CoordinadorCentral(session)
    
    # Test personalización básica
    content_template = "Hola {user_name}, Diana {emotional_response}"
    context = {
        "user_name": "TestUser",
        "emotional_response": "sonríe cálidamente"
    }
    
    try:
        personalized = await coordinator.content_delivery_service.personalize_content(
            content_template, context
        )
        print(f"Template: {content_template}")
        print(f"Resultado: {personalized}")
        
        # Verificar que se reemplazaron las variables
        if "{" in personalized and "}" in personalized:
            print("WARNING: Variables no reemplazadas completamente")
            return False
            
        return True
        
    except Exception as e:
        print(f"Error en personalización: {e}")
        return False
```

**Soluciones:**

1. **Problema con formato de variables:**
```python
# Las variables deben estar en formato {variable_name}
# Formato incorrecto: {{variable_name}} o %variable_name%
# Formato correcto: {variable_name}

async def fix_content_template_format(template: str) -> str:
    import re
    
    # Detectar y corregir formatos incorrectos
    fixed_template = template
    
    # Corregir formato doble {{variable}}
    fixed_template = re.sub(r'\{\{(\w+)\}\}', r'{\1}', fixed_template)
    
    # Corregir formato %variable%
    fixed_template = re.sub(r'%(\w+)%', r'{\1}', fixed_template)
    
    print(f"Original: {template}")
    print(f"Corregido: {fixed_template}")
    
    return fixed_template
```

2. **Problema con contexto de personalización:**
```python
async def test_emotional_context_delivery(user_id: int):
    coordinator = CoordinadorCentral(session)
    
    # Obtener contexto emocional
    emotional_context = await coordinator.emotional_state_service.get_user_emotional_state(user_id)
    recommended_tone = await coordinator.emotional_state_service.get_recommended_content_tone(user_id)
    
    print(f"Estado emocional: {emotional_context.primary_state.value}")
    print(f"Tono recomendado: {recommended_tone}")
    
    # Test de preparación de contenido
    content_package = await coordinator.content_delivery_service.prepare_content(
        "test_content",
        {
            "text": "Diana {emotional_response} mientras observa tu {emotional_state}.",
            "emotional_state": emotional_context.primary_state.value,
            "emotional_response": _get_emotional_response_text(recommended_tone)
        }
    )
    
    print(f"Contenido preparado: {content_package.payload}")
```

### Problema 4: Falla en entrega de contenido

**Síntomas:**
- `deliver_content()` retorna `False`
- Mensajes no llegan al usuario
- Errores de serialización en `ContentPackage`

**Diagnóstico:**
```python
async def diagnose_content_delivery_failure(user_id: int, bot):
    coordinator = CoordinadorCentral(session)
    
    try:
        # Test de preparación
        package = await coordinator.content_delivery_service.prepare_content(
            "test_delivery",
            {"text": "Mensaje de prueba"}
        )
        print(f"Contenido preparado exitosamente: {package.content_id}")
        
        # Test de validación
        valid, errors = await coordinator.content_delivery_service.validate_delivery_constraints(
            package, {"bot": bot, "chat_id": user_id}
        )
        
        if not valid:
            print(f"Restricciones de entrega fallidas: {errors}")
            return False
        
        # Test de entrega
        success = await coordinator.content_delivery_service.deliver_content(
            package, {"bot": bot, "chat_id": user_id}
        )
        
        if not success:
            print("Entrega falló - verificar logs del bot")
            return False
        
        print("Entrega exitosa")
        return True
        
    except Exception as e:
        print(f"Error en diagnóstico de entrega: {e}")
        return False
```

**Solución:**
```python
async def fix_content_delivery_issues():
    # 1. Verificar que el bot está disponible
    if not bot:
        print("ERROR: Bot instance no está disponible")
        return
    
    # 2. Verificar permisos del bot
    try:
        bot_info = await bot.get_me()
        print(f"Bot conectado: {bot_info.username}")
    except Exception as e:
        print(f"Error conectando con bot: {e}")
        return
    
    # 3. Test de envío básico
    try:
        test_message = await bot.send_message(chat_id=user_id, text="Test de conectividad")
        print(f"Test message sent: {test_message.message_id}")
    except Exception as e:
        print(f"Error enviando mensaje de prueba: {e}")
```

## Problemas de Procesamiento de Interacciones

### Problema 5: Interacciones no se procesan

**Síntomas:**
- `process_interaction()` lanza excepción
- `InteractionResult.success = False` siempre
- No se registran interacciones en historial

**Diagnóstico:**
```python
async def diagnose_interaction_processing(user_id: int):
    coordinator = CoordinadorCentral(session)
    
    # Test de validación de interacción
    test_context = InteractionContext(
        user_id=user_id,
        interaction_type=InteractionType.MESSAGE,
        raw_data={"text": "test message", "message_id": 123},
        timestamp=datetime.now(),
        session_data={}
    )
    
    # 1. Test validación
    try:
        is_valid, errors = await coordinator.interaction_processor.validate_user_interaction(test_context)
        print(f"Validación: {'Válida' if is_valid else 'Inválida'}")
        if errors:
            print(f"Errores: {errors}")
    except Exception as e:
        print(f"Error en validación: {e}")
    
    # 2. Test procesamiento
    try:
        result = await coordinator.interaction_processor.process_interaction(test_context)
        print(f"Procesamiento: {'Exitoso' if result.success else 'Falló'}")
        print(f"Datos de respuesta: {result.response_data}")
    except Exception as e:
        print(f"Error en procesamiento: {e}")
    
    # 3. Test historial
    try:
        history = await coordinator.interaction_processor.get_user_interaction_history(user_id, 5)
        print(f"Historial disponible: {len(history)} interacciones")
    except Exception as e:
        print(f"Error obteniendo historial: {e}")
```

**Soluciones:**

1. **Problema con dependencies del processor:**
```python
async def fix_interaction_processor_dependencies():
    coordinator = CoordinadorCentral(session)
    
    # Verificar que las dependencias están configuradas
    processor = coordinator.interaction_processor
    
    if not hasattr(processor, '_service') or processor._service is None:
        print("WARNING: UserInteractionService no inicializado")
        # Forzar inicialización
        _ = processor._get_service()
    
    # Configurar dependencias si no están configuradas
    service = processor._get_service()
    
    if service.emotional_manager is None:
        processor.set_dependencies(emotional_manager=coordinator.emotional_state_service)
        print("Emotional manager configurado")
    
    if service.point_service is None:
        processor.set_dependencies(point_service=coordinator.point_service)
        print("Point service configurado")
```

2. **Problema con formato de InteractionContext:**
```python
def create_valid_interaction_context(user_id: int, interaction_data: Dict[str, Any]) -> InteractionContext:
    """Crea un InteractionContext válido desde datos de interacción."""
    
    # Determinar tipo de interacción
    interaction_type = InteractionType.MESSAGE  # Default
    
    if "callback_data" in interaction_data:
        interaction_type = InteractionType.CALLBACK
    elif "command" in interaction_data:
        interaction_type = InteractionType.COMMAND
    elif "emoji" in interaction_data:
        interaction_type = InteractionType.REACTION
    
    # Crear contexto válido
    return InteractionContext(
        user_id=user_id,
        interaction_type=interaction_type,
        raw_data=interaction_data,
        timestamp=datetime.now(),
        session_data={}
    )
```

## Problemas del EventBus

### Problema 6: Eventos no se publican o reciben

**Síntomas:**
- Subscribers no reciben eventos
- `publish()` no lanza errores pero eventos no llegan
- Event history está vacía

**Diagnóstico:**
```python
def diagnose_event_bus():
    event_bus = get_event_bus()
    
    # 1. Verificar estado del event bus
    print(f"Event bus instance: {event_bus}")
    print(f"Subscribers registrados: {len(event_bus._subscribers)}")
    
    # 2. Verificar suscripciones por tipo
    for event_type, subscribers in event_bus._subscribers.items():
        print(f"  {event_type.value}: {len(subscribers)} subscribers")
    
    # 3. Verificar historial
    history = event_bus.get_event_history(10)
    print(f"Eventos recientes: {len(history)}")
    
    for event in history[-5:]:  # Últimos 5 eventos
        print(f"  {event.timestamp}: {event.event_type.value} - User {event.user_id}")

# Test de publicación y suscripción
async def test_event_publication():
    event_bus = get_event_bus()
    received_events = []
    
    # Handler de test
    async def test_handler(event: Event):
        received_events.append(event)
        print(f"Evento recibido: {event.event_type.value}")
    
    # Suscribirse
    event_bus.subscribe(EventType.POINTS_AWARDED, test_handler)
    
    # Publicar evento de test
    await event_bus.publish(
        EventType.POINTS_AWARDED,
        123456,
        {"points": 10, "test": True},
        source="troubleshooting"
    )
    
    # Esperar procesamiento asíncrono
    await asyncio.sleep(0.1)
    
    if received_events:
        print(f"SUCCESS: {len(received_events)} eventos recibidos")
        return True
    else:
        print("FAILURE: No se recibieron eventos")
        return False
```

**Soluciones:**

1. **Reset del EventBus:**
```python
def reset_event_bus_if_needed():
    from services.event_bus import reset_event_bus
    
    # Reset global instance
    reset_event_bus()
    
    # Crear nueva instancia
    new_event_bus = get_event_bus()
    print(f"EventBus reseteado. Nueva instancia: {new_event_bus}")
```

2. **Debugging de handlers que fallan:**
```python
async def debug_failing_handlers():
    event_bus = get_event_bus()
    
    # Test cada tipo de evento
    test_events = [
        (EventType.POINTS_AWARDED, {"points": 1}),
        (EventType.USER_REACTION, {"reaction": "test"}),
        (EventType.WORKFLOW_COMPLETED, {"workflow": "test"})
    ]
    
    for event_type, data in test_events:
        try:
            await event_bus.publish(event_type, 123456, data, source="debug")
            print(f"✓ {event_type.value}: OK")
        except Exception as e:
            print(f"✗ {event_type.value}: Error - {e}")
```

### Problema 7: Memory leaks en suscripciones

**Síntomas:**
- Uso de memoria aumenta constantemente
- Rendimiento degrada con el tiempo
- Demasiadas suscripciones activas

**Diagnóstico:**
```python
def diagnose_subscription_memory_leaks():
    from docs.escenarios_integracion_avanzados import get_subscription_manager
    
    sub_manager = get_subscription_manager()
    stats = sub_manager.get_subscription_stats()
    
    print(f"Total suscripciones: {stats['total_subscriptions']}")
    print(f"Activas: {stats['active_subscriptions']}")
    print(f"Inactivas: {stats['inactive_subscriptions']}")
    print(f"Por tipo de evento: {stats['subscriptions_by_event_type']}")
    
    # Alerta si hay demasiadas suscripciones
    if stats['total_subscriptions'] > 1000:
        print("WARNING: Demasiadas suscripciones, posible memory leak")
        return True
    
    return False
```

**Solución:**
```python
async def cleanup_subscription_memory_leaks():
    from docs.escenarios_integracion_avanzados import get_subscription_manager
    
    sub_manager = get_subscription_manager()
    
    # Forzar cleanup
    await sub_manager._cleanup_expired_subscriptions()
    
    # Estadísticas después del cleanup
    stats = sub_manager.get_subscription_stats()
    print(f"Después del cleanup: {stats['active_subscriptions']} activas")
```

## Problemas de Integración CoordinadorCentral

### Problema 8: Workflows fallan parcialmente

**Síntomas:**
- `ejecutar_flujo()` retorna success=False
- Algunos servicios funcionan, otros no
- Inconsistencias entre módulos

**Diagnóstico:**
```python
async def diagnose_coordinator_workflow_failures(user_id: int):
    coordinator = CoordinadorCentral(session)
    
    # Test de servicios individuales
    services_to_test = [
        ("emotional_state_service", coordinator.emotional_state_service),
        ("content_delivery_service", coordinator.content_delivery_service),
        ("interaction_processor", coordinator.interaction_processor),
        ("point_service", coordinator.point_service),
        ("narrative_service", coordinator.narrative_service)
    ]
    
    service_status = {}
    
    for service_name, service in services_to_test:
        try:
            # Test básico de cada servicio
            if service_name == "emotional_state_service":
                await service.get_user_emotional_state(user_id)
            elif service_name == "point_service":
                await service.get_user_points(user_id)
            elif service_name == "narrative_service":
                await service.get_user_current_fragment(user_id)
            # Los demás servicios no tienen métodos de test directo
            
            service_status[service_name] = "OK"
            
        except Exception as e:
            service_status[service_name] = f"ERROR: {str(e)}"
    
    print("Estado de servicios:")
    for service, status in service_status.items():
        print(f"  {service}: {status}")
    
    # Test de flujo específico
    try:
        result = await coordinator.ejecutar_flujo(
            user_id,
            AccionUsuario.ANALIZAR_ESTADO_EMOCIONAL,
            interaction_data={"type": "test", "source": "troubleshooting"}
        )
        
        print(f"Test de flujo: {'SUCCESS' if result['success'] else 'FAILED'}")
        if not result['success']:
            print(f"  Error: {result.get('error')}")
            
    except Exception as e:
        print(f"Test de flujo: EXCEPTION - {e}")
```

**Soluciones:**

1. **Reinicialización de servicios:**
```python
async def reinitialize_coordinator_services(session: AsyncSession):
    """Reinicializa CoordinadorCentral con servicios frescos."""
    
    try:
        # Crear nuevo coordinador
        new_coordinator = CoordinadorCentral(session)
        
        # Verificar que todos los servicios se inicializaron
        required_services = [
            'emotional_state_service',
            'content_delivery_service', 
            'interaction_processor',
            'point_service',
            'narrative_service',
            'event_bus'
        ]
        
        for service_name in required_services:
            service = getattr(new_coordinator, service_name, None)
            if service is None:
                print(f"WARNING: {service_name} no inicializado")
            else:
                print(f"✓ {service_name}: {type(service).__name__}")
        
        return new_coordinator
        
    except Exception as e:
        print(f"Error reinicializando coordinador: {e}")
        return None
```

2. **Healing de inconsistencias:**
```python
async def heal_coordinator_inconsistencies(coordinator: CoordinadorCentral, user_id: int):
    """Repara inconsistencias detectadas en el coordinador."""
    
    # Ejecutar consistency check
    consistency_report = await coordinator.check_system_consistency(user_id)
    
    print(f"Consistency check para usuario {user_id}:")
    print(f"  Issues encontrados: {consistency_report['checks']['issues_found']}")
    print(f"  Issues corregidos: {consistency_report['checks']['issues_corrected']}")
    
    # Si hay errores críticos, reportar
    if consistency_report.get("errors"):
        print("Errores críticos encontrados:")
        for error in consistency_report["errors"]:
            print(f"  - {error}")
    
    # Si hay warnings, reportar
    if consistency_report.get("warnings"):
        print("Warnings encontrados:")
        for warning in consistency_report["warnings"]:
            print(f"  - {warning}")
    
    return consistency_report
```

## Problemas de Performance

### Problema 9: Workflows lentos

**Síntomas:**
- Timeouts en operaciones
- Usuarios reportan respuestas lentas
- Alto uso de CPU/memoria

**Diagnóstico:**
```python
import time
import asyncio
from functools import wraps

def performance_monitor(func):
    """Decorator para monitorear performance de funciones async."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        memory_before = psutil.Process().memory_info().rss if 'psutil' in globals() else 0
        
        try:
            result = await func(*args, **kwargs)
            
            end_time = time.time()
            memory_after = psutil.Process().memory_info().rss if 'psutil' in globals() else 0
            
            execution_time = end_time - start_time
            memory_diff = memory_after - memory_before
            
            print(f"Performance [{func.__name__}]:")
            print(f"  Execution time: {execution_time:.3f}s")
            print(f"  Memory delta: {memory_diff / 1024 / 1024:.2f} MB")
            
            # Alertar si es muy lento
            if execution_time > 5.0:
                print(f"  WARNING: Slow execution ({execution_time:.1f}s)")
            
            return result
            
        except Exception as e:
            end_time = time.time()
            print(f"Performance [{func.__name__}] FAILED after {end_time - start_time:.3f}s: {e}")
            raise
            
    return wrapper

# Usar el decorator en funciones que sospechamos son lentas
@performance_monitor
async def test_workflow_performance(coordinator: CoordinadorCentral, user_id: int):
    """Test de performance de workflow complejo."""
    
    result = await coordinator.ejecutar_flujo_async(
        user_id,
        AccionUsuario.COMPLETAR_FRAGMENTO_NARRATIVO,
        fragment_id="test_fragment",
        correlation_id="performance_test"
    )
    
    return result
```

**Soluciones:**

1. **Optimización de queries de base de datos:**
```python
async def optimize_database_queries():
    """Sugerencias para optimizar queries lentos."""
    
    # 1. Verificar índices en tablas críticas
    critical_tables = [
        "users",
        "user_emotional_states", 
        "user_narrative_states",
        "emotional_state_history"
    ]
    
    for table in critical_tables:
        print(f"Verificar índices en tabla {table}:")
        print(f"  - user_id (debe tener índice)")
        print(f"  - created_at/updated_at (para queries por fecha)")
    
    # 2. Usar select específico en lugar de select *
    print("\nOptimización de queries:")
    print("  ✗ BAD:  select * from users")
    print("  ✓ GOOD: select id, name, points from users")
    
    # 3. Usar eager loading para relaciones
    print("\n  ✗ BAD:  N+1 queries")
    print("  ✓ GOOD: Join queries o selectinload()")
```

2. **Implementar cache para operaciones frecuentes:**
```python
from typing import Optional
import asyncio

class SimpleAsyncCache:
    def __init__(self, ttl_seconds: int = 300):  # 5 minutes default
        self.cache = {}
        self.ttl = ttl_seconds
    
    async def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                del self.cache[key]
        return None
    
    async def set(self, key: str, value: Any):
        self.cache[key] = (value, time.time())
    
    def clear(self):
        self.cache.clear()

# Implementar cache en servicios críticos
emotional_state_cache = SimpleAsyncCache(ttl_seconds=60)  # 1 minuto

async def cached_get_emotional_state(service, user_id: int):
    cache_key = f"emotional_state_{user_id}"
    
    # Check cache first
    cached_result = await emotional_state_cache.get(cache_key)
    if cached_result:
        return cached_result
    
    # Si no está en cache, obtener de base de datos
    result = await service.get_user_emotional_state(user_id)
    
    # Guardar en cache
    await emotional_state_cache.set(cache_key, result)
    
    return result
```

## Problemas de Base de Datos

### Problema 10: Errores de conexión a BD

**Síntomas:**
- `sqlalchemy.exc.DisconnectionError`
- Timeouts en queries
- Connection pool exhausted

**Diagnóstico:**
```python
async def diagnose_database_connection(session: AsyncSession):
    """Diagnóstica problemas de conexión a base de datos."""
    
    try:
        # Test de conectividad básico
        result = await session.execute(text("SELECT 1"))
        scalar_result = result.scalar()
        print(f"✓ Conectividad básica: {scalar_result}")
        
        # Test de transacción
        async with session.begin():
            result = await session.execute(text("SELECT COUNT(*) FROM users"))
            count = result.scalar()
            print(f"✓ Transacción exitosa, {count} usuarios en DB")
        
        # Test de performance de query
        start_time = time.time()
        result = await session.execute(
            text("SELECT id, created_at FROM users ORDER BY created_at DESC LIMIT 10")
        )
        users = result.fetchall()
        query_time = time.time() - start_time
        
        print(f"✓ Query performance: {query_time:.3f}s para {len(users)} registros")
        
        if query_time > 1.0:
            print("WARNING: Query lento, considerar optimización")
        
        return True
        
    except Exception as e:
        print(f"✗ Error de base de datos: {e}")
        print(f"  Tipo: {type(e).__name__}")
        
        # Diagnóstico específico por tipo de error
        if "timeout" in str(e).lower():
            print("  Sugerencia: Aumentar timeout o optimizar queries")
        elif "connection" in str(e).lower():
            print("  Sugerencia: Verificar configuración de connection pool")
        elif "lock" in str(e).lower():
            print("  Sugerencia: Posible deadlock, revisar orden de queries")
            
        return False
```

**Soluciones:**

1. **Configuración de connection pool:**
```python
# En la configuración de SQLAlchemy
from sqlalchemy.pool import QueuePool

# Configuración recomendada para production
engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,          # Número de conexiones persistentes
    max_overflow=10,       # Conexiones adicionales permitidas
    pool_timeout=30,       # Timeout para obtener conexión del pool
    pool_recycle=1800,     # Reciclar conexiones cada 30 min
    echo=False             # Set True solo para debugging
)
```

2. **Retry logic para operaciones críticas:**
```python
import asyncio
from functools import wraps

def database_retry(max_retries: int = 3, delay: float = 1.0):
    """Decorator para retry automático en operaciones de base de datos."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Solo retry en ciertos tipos de errores
                    if "timeout" in str(e).lower() or "connection" in str(e).lower():
                        if attempt < max_retries - 1:  # No delay en último intento
                            print(f"Database operation failed (attempt {attempt + 1}), retrying in {delay}s...")
                            await asyncio.sleep(delay * (attempt + 1))  # Backoff exponencial
                            continue
                    
                    # Si no es un error de retry o último intento, re-raise
                    raise
            
            # Si llegamos aquí, todos los intentos fallaron
            raise last_exception
            
        return wrapper
    return decorator

# Uso del decorator
@database_retry(max_retries=3, delay=1.0)
async def robust_get_user_points(point_service, user_id: int) -> int:
    return await point_service.get_user_points(user_id)
```

## Herramientas de Debugging

### Debug Console

```python
class InterfaceDebugConsole:
    """Consola interactiva para debugging del sistema de interfaces."""
    
    def __init__(self, coordinator: CoordinadorCentral):
        self.coordinator = coordinator
        self.commands = {
            'status': self.show_status,
            'emotional': self.debug_emotional_state,
            'events': self.show_recent_events,
            'health': self.health_check,
            'test': self.run_tests,
            'reset': self.reset_services,
            'help': self.show_help
        }
    
    async def run(self):
        """Ejecuta la consola interactiva."""
        print("=== Interface Debug Console ===")
        print("Escribe 'help' para ver comandos disponibles")
        
        while True:
            try:
                command = input("\ndebug> ").strip().lower()
                
                if command == 'exit':
                    print("Saliendo del debug console...")
                    break
                
                if command in self.commands:
                    await self.commands[command]()
                else:
                    print(f"Comando desconocido: {command}")
                    await self.show_help()
                    
            except KeyboardInterrupt:
                print("\nSaliendo del debug console...")
                break
            except Exception as e:
                print(f"Error ejecutando comando: {e}")
    
    async def show_status(self):
        """Muestra estado general del sistema."""
        status = await self.coordinator.get_coordination_status()
        
        print("\n=== System Status ===")
        print(f"CoordinadorCentral: {'Active' if status['coordinador_central']['active'] else 'Inactive'}")
        print(f"Session: {'Active' if status['coordinador_central']['session_active'] else 'Inactive'}")
        
        services = status['coordinador_central']['services_loaded']
        print("\nServices:")
        for service, loaded in services.items():
            print(f"  {service}: {'✓' if loaded else '✗'}")
        
        event_system = status.get('event_system', {})
        print(f"\nEventBus subscriptions: {event_system.get('total_subscriptions', 'Unknown')}")
    
    async def debug_emotional_state(self):
        """Debug de estados emocionales."""
        user_id = input("User ID: ")
        try:
            user_id = int(user_id)
            
            # Obtener estado actual
            context = await self.coordinator.emotional_state_service.get_user_emotional_state(user_id)
            
            print(f"\n=== Emotional State for User {user_id} ===")
            print(f"Primary State: {context.primary_state.value}")
            print(f"Intensity: {context.intensity}")
            print(f"Last Updated: {context.last_updated}")
            print(f"Triggers: {context.triggers}")
            
            if context.secondary_states:
                print("Secondary States:")
                for state, intensity in context.secondary_states.items():
                    print(f"  {state.value}: {intensity}")
            
            # Test de análisis
            test_data = {"type": "test", "source": "debug_console"}
            inferred = await self.coordinator.emotional_state_service.analyze_interaction_emotion(user_id, test_data)
            print(f"\nInferred emotion for test interaction: {inferred.value}")
            
        except ValueError:
            print("User ID debe ser un número")
        except Exception as e:
            print(f"Error: {e}")
    
    async def show_recent_events(self):
        """Muestra eventos recientes del EventBus."""
        limit = input("Número de eventos (default 10): ")
        try:
            limit = int(limit) if limit else 10
            
            events = self.coordinator.event_bus.get_event_history(limit)
            
            print(f"\n=== Recent {len(events)} Events ===")
            for event in reversed(events):  # Más recientes primero
                print(f"{event.timestamp.strftime('%H:%M:%S')} | "
                      f"{event.event_type.value:20} | "
                      f"User {event.user_id:8} | "
                      f"Source: {event.source or 'unknown'}")
                
                if event.correlation_id:
                    print(f"    Correlation: {event.correlation_id}")
                
                if event.data:
                    print(f"    Data: {event.data}")
                print()
                
        except ValueError:
            print("Límite debe ser un número")
        except Exception as e:
            print(f"Error: {e}")
    
    async def health_check(self):
        """Ejecuta health check comprehensivo."""
        print("\n=== Running Health Check ===")
        
        health_report = await self.coordinator.perform_system_health_check()
        
        print(f"Overall Status: {health_report['overall_status']}")
        
        if health_report.get('modules'):
            print("\nModule Status:")
            for module, status in health_report['modules'].items():
                print(f"  {module}: {status.get('status', 'unknown')}")
                if status.get('error'):
                    print(f"    Error: {status['error']}")
        
        if health_report.get('recommendations'):
            print("\nRecommendations:")
            for rec in health_report['recommendations']:
                print(f"  - {rec}")
    
    async def run_tests(self):
        """Ejecuta tests de integración."""
        print("\n=== Running Integration Tests ===")
        
        # Test básico de cada interfaz
        test_user_id = 123456789  # Usuario de test
        
        tests = [
            ("Emotional State Service", self.test_emotional_service),
            ("Content Delivery Service", self.test_content_service),
            ("Event Bus", self.test_event_bus),
            ("Coordinator Workflows", self.test_coordinator_workflows)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            try:
                result = await test_func(test_user_id)
                results[test_name] = "✓ PASS" if result else "✗ FAIL"
                print(f"{test_name}: {results[test_name]}")
            except Exception as e:
                results[test_name] = f"✗ ERROR: {str(e)}"
                print(f"{test_name}: {results[test_name]}")
        
        print(f"\n=== Test Summary ===")
        for test_name, result in results.items():
            print(f"{test_name}: {result}")
    
    async def test_emotional_service(self, user_id: int) -> bool:
        """Test del servicio de estados emocionales."""
        try:
            # Test obtener estado
            context = await self.coordinator.emotional_state_service.get_user_emotional_state(user_id)
            
            # Test análisis de interacción
            test_data = {"type": "test", "source": "integration_test"}
            inferred = await self.coordinator.emotional_state_service.analyze_interaction_emotion(user_id, test_data)
            
            # Test tono recomendado
            tone = await self.coordinator.emotional_state_service.get_recommended_content_tone(user_id)
            
            return context is not None and inferred is not None and tone is not None
            
        except Exception as e:
            print(f"    Emotional service error: {e}")
            return False
    
    async def test_content_service(self, user_id: int) -> bool:
        """Test del servicio de content delivery."""
        try:
            service = self.coordinator.content_delivery_service
            
            # Test preparar contenido
            package = await service.prepare_content("test_content", {"text": "Test message {user_id}", "user_id": user_id})
            
            # Test personalizar contenido
            personalized = await service.personalize_content("Hello {name}", {"name": "TestUser"})
            
            # Test validar restricciones
            valid, errors = await service.validate_delivery_constraints(package, {})
            
            return package is not None and personalized == "Hello TestUser" and valid
            
        except Exception as e:
            print(f"    Content service error: {e}")
            return False
    
    async def test_event_bus(self) -> bool:
        """Test del EventBus."""
        try:
            event_bus = self.coordinator.event_bus
            
            # Test publicar evento
            event = await event_bus.publish(
                EventType.POINTS_AWARDED,
                123456,
                {"points": 1, "test": True},
                source="integration_test"
            )
            
            # Verificar que se guardó en history
            history = event_bus.get_event_history(5)
            recent_event = next((e for e in history if e.event_id == event.event_id), None)
            
            return event is not None and recent_event is not None
            
        except Exception as e:
            print(f"    Event bus error: {e}")
            return False
    
    async def test_coordinator_workflows(self, user_id: int) -> bool:
        """Test de workflows del coordinador."""
        try:
            # Test workflow de análisis emocional
            result = await self.coordinator.ejecutar_flujo(
                user_id,
                AccionUsuario.ANALIZAR_ESTADO_EMOCIONAL,
                interaction_data={"type": "test", "source": "integration_test"}
            )
            
            return result.get("success", False)
            
        except Exception as e:
            print(f"    Coordinator workflow error: {e}")
            return False
    
    async def reset_services(self):
        """Reset de servicios (solo para debugging)."""
        confirm = input("¿Resetear servicios? (y/N): ")
        if confirm.lower() == 'y':
            try:
                # Reset EventBus
                from services.event_bus import reset_event_bus
                reset_event_bus()
                self.coordinator.event_bus = get_event_bus()
                
                # Clear caches si existen
                if hasattr(self.coordinator, '_cache'):
                    self.coordinator._cache.clear()
                
                print("Servicios reseteados")
                
            except Exception as e:
                print(f"Error reseteando servicios: {e}")
        else:
            print("Reset cancelado")
    
    async def show_help(self):
        """Muestra ayuda de comandos."""
        print("\n=== Available Commands ===")
        print("status      - Muestra estado general del sistema")
        print("emotional   - Debug de estados emocionales de usuario")
        print("events      - Muestra eventos recientes del EventBus")
        print("health      - Ejecuta health check comprehensivo")
        print("test        - Ejecuta tests de integración")
        print("reset       - Reset de servicios (debugging only)")
        print("help        - Muestra esta ayuda")
        print("exit        - Salir del debug console")

# Función utilitaria para iniciar debug console
async def start_debug_console(coordinator: CoordinadorCentral):
    """Inicia la consola de debugging."""
    console = InterfaceDebugConsole(coordinator)
    await console.run()
```

### Script de Diagnóstico Automático

```python
async def run_automated_diagnostics(session: AsyncSession, user_id: int = None):
    """
    Ejecuta diagnósticos automáticos de todo el sistema de interfaces.
    
    Args:
        session: Sesión de base de datos
        user_id: ID de usuario específico para tests (opcional)
    """
    
    print("=== AUTOMATED DIAGNOSTICS ===")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Test user ID: {user_id or 'N/A'}")
    print()
    
    coordinator = CoordinadorCentral(session)
    issues_found = []
    
    # 1. Test de conectividad de base de datos
    print("1. Database Connectivity...")
    db_ok = await diagnose_database_connection(session)
    if not db_ok:
        issues_found.append("Database connectivity issues")
    
    # 2. Test de servicios básicos
    print("\n2. Core Services...")
    service_tests = [
        ("CoordinadorCentral", coordinator is not None),
        ("EventBus", coordinator.event_bus is not None),
        ("EmotionalStateService", coordinator.emotional_state_service is not None),
        ("ContentDeliveryService", coordinator.content_delivery_service is not None),
        ("InteractionProcessor", coordinator.interaction_processor is not None)
    ]
    
    for service_name, service_ok in service_tests:
        status = "✓" if service_ok else "✗"
        print(f"  {status} {service_name}")
        if not service_ok:
            issues_found.append(f"{service_name} not initialized")
    
    # 3. Test de EventBus
    print("\n3. EventBus...")
    event_ok = await test_event_publication()
    if not event_ok:
        issues_found.append("EventBus not working correctly")
    
    # 4. Test con usuario específico (si se proporciona)
    if user_id:
        print(f"\n4. User-Specific Tests (User {user_id})...")
        
        try:
            # Test estado emocional
            emotional_ok = await diagnose_emotional_consistency(user_id)
            if not emotional_ok:
                issues_found.append(f"Emotional state issues for user {user_id}")
            
            # Test workflow básico
            result = await coordinator.ejecutar_flujo(
                user_id,
                AccionUsuario.ANALIZAR_ESTADO_EMOCIONAL,
                interaction_data={"type": "diagnostic", "source": "automated_test"}
            )
            
            if not result.get("success", False):
                issues_found.append(f"Workflow execution failed for user {user_id}")
                
        except Exception as e:
            issues_found.append(f"User-specific tests failed: {str(e)}")
    
    # 5. Health check general
    print("\n5. System Health Check...")
    try:
        health_report = await coordinator.perform_system_health_check()
        if health_report["overall_status"] != "healthy":
            issues_found.append(f"System health: {health_report['overall_status']}")
            
            if health_report.get("recommendations"):
                print("  Recommendations:")
                for rec in health_report["recommendations"]:
                    print(f"    - {rec}")
                    
    except Exception as e:
        issues_found.append(f"Health check failed: {str(e)}")
    
    # 6. Memory y performance check
    print("\n6. Performance Check...")
    try:
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        cpu_percent = process.cpu_percent()
        
        print(f"  Memory usage: {memory_mb:.1f} MB")
        print(f"  CPU usage: {cpu_percent:.1f}%")
        
        if memory_mb > 500:  # Más de 500MB
            issues_found.append(f"High memory usage: {memory_mb:.1f} MB")
        if cpu_percent > 80:  # Más de 80% CPU
            issues_found.append(f"High CPU usage: {cpu_percent:.1f}%")
            
    except ImportError:
        print("  psutil not available, skipping performance check")
    except Exception as e:
        print(f"  Performance check error: {e}")
    
    # Resumen final
    print("\n" + "="*50)
    print("DIAGNOSTIC SUMMARY")
    print("="*50)
    
    if not issues_found:
        print("✓ All systems operational")
        return True
    else:
        print(f"✗ {len(issues_found)} issues found:")
        for i, issue in enumerate(issues_found, 1):
            print(f"  {i}. {issue}")
        
        print("\nRecommended actions:")
        print("  1. Review logs for detailed error information")
        print("  2. Run individual diagnostic functions for failing components")
        print("  3. Consider restarting services if issues persist")
        print("  4. Check database connectivity and performance")
        
        return False

# Para usar desde línea de comandos
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Configurar sesión de base de datos
        from database.database import get_session
        
        async with get_session() as session:
            success = await run_automated_diagnostics(session, user_id=123456789)
            exit(0 if success else 1)
    
    asyncio.run(main())
```

---

*Esta guía de troubleshooting cubre los problemas más comunes observados en el sistema de interfaces implementado y proporciona soluciones probadas basadas en el código real.*