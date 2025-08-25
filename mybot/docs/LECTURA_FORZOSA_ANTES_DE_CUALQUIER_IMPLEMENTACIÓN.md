# GUÍA DE IMPLEMENTACIÓN: SISTEMA NARRATIVO UNIFICADO

## Resumen Ejecutivo

El sistema de narrativa se ha unificado completamente eliminando la duplicación de modelos. Este documento explica los cambios críticos y patrones de implementación.

## 1. Modelo de Datos Unificado

### NarrativeFragment (Modelo Único)

El modelo `NarrativeFragment` en `database/narrative_unified.py` ahora reemplaza todos los modelos narrativos anteriores:

```python
# Inicializar fragmento narrativo unificado
fragment = NarrativeFragment(
    title="Título del fragmento",
    content="Contenido del fragmento...",
    fragment_type="STORY",  # Tipos: STORY, DECISION, INFO
    choices=[{"text": "Opción 1", "next_id": "uuid-destino"}],
    triggers={"reward": {"points": 10, "clues": ["CODE1"]}},
    required_clues=["PISTA1", "PISTA2"]
)
```

**Características clave:**
- UUID como identificador único global
- Campo `fragment_type` clasifica los fragmentos (STORY, DECISION, INFO)
- JSON para `choices`, `triggers` y `required_clues`
- Índices optimizados para consultas frecuentes

### UserNarrativeState (Estado Unificado)

El modelo `UserNarrativeState` rastrea todo el progreso del usuario:

```python
# Verificar progreso del usuario
async def check_progress(user_id, session):
    state = await session.get(UserNarrativeState, user_id)
    if not state:
        state = UserNarrativeState(user_id=user_id)
        session.add(state)
    
    # Calcular progreso
    progress = state.get_progress_percentage(session)
    # Verificar pistas desbloqueadas
    has_clue = state.has_unlocked_clue("CODE1")
    
    return progress, has_clue
```

## 2. Patrones de Implementación

### Patrón: Manejo de Fragmentos

```python
# 1. Obtener fragmento actual
fragment = await session.get(NarrativeFragment, fragment_id)

# 2. Verificar requisitos
for clue_code in fragment.required_clues:
    if not user_state.has_unlocked_clue(clue_code):
        raise ValueError(f"Se requiere la pista {clue_code}")

# 3. Procesar triggers/rewards
if fragment.triggers:
    await process_triggers(user_id, fragment.triggers, session)

# 4. Actualizar estado del usuario
user_state.visited_fragments.append(fragment.id)
if fragment.is_story:
    user_state.completed_fragments.append(fragment.id)
```

### Patrón: Desbloqueo de Pistas

```python
# Implementación centralizada del desbloqueo de pistas
async def unlock_clue(user_id, clue_code, session):
    user_state = await get_user_narrative_state(user_id, session)
    
    if clue_code in user_state.unlocked_clues:
        return False  # Ya desbloqueada
    
    user_state.unlocked_clues.append(clue_code)
    await session.commit()
    
    # Notificar desbloqueo (usar NotificationService)
    await notification_service.add_notification(
        user_id=user_id,
        type="clue_unlocked",
        data={"clue_code": clue_code}
    )
    
    return True
```

## 3. Flujos de Datos

### Navegación Narrativa
1. Usuario interactúa con fragmento actual → `handlers/user_narrative_handler.py`
2. Servicio actualiza estado → `services/user_narrative_service.py`
3. Se procesan triggers (recompensas, pistas) → `services/reward_service.py`
4. Se actualiza UserNarrativeState → `database/narrative_unified.py`

### Desbloqueo de Pistas
1. Origen: Completar fragmentos, códigos manuales, misiones
2. Centralizado en UserNarrativeService.unlock_clue()
3. Actualización en UserNarrativeState.unlocked_clues
4. Notificación vía NotificationService

## 4. Integración con Sistemas Existentes

### Sistema de Puntos
- Puntos narrativos se procesan vía `services/point_service.py`
- Se mantiene `PointTransaction` para auditoría completa

### Misiones
- Triggers narrativos pueden completar objetivos de misiones
- Interfaz centralizada en `services/unified_mission_service.py`

## 5. ADR: Unificación de Modelos Narrativos

### Contexto
Múltiples modelos (StoryFragment, NarrativeFragment, NarrativeChoice) generaban confusión, inconsistencias y bugs.

### Decisión
Unificar en un solo modelo NarrativeFragment con soporte para todos los tipos mediante campos estructurados JSON.

### Consecuencias
**Beneficios:**
- Consultas simplificadas (un solo modelo)
- Eliminación de joins complejos
- Mejor trazabilidad del progreso del usuario

**Consideraciones:**
- Requiere migración de datos existentes
- Actualización de servicios dependientes

## 6. Verificación de Implementación

Antes de integrar código nuevo, verificar:

1. **Pruebas unitarias**: Ejecutar tests específicos
   ```bash
   python -m unittest tests.services.test_user_narrative_service
   ```

2. **Integridad de datos**: Ejecutar script de reconciliación
   ```bash
   python scripts/verify_unified_narrative.py
   ```

3. **Compatibilidad API**: Verificar llamadas existentes
   ```python
   # Las llamadas deberían funcionar igual con el nuevo modelo
   await narrative_service.get_user_progress(user_id)
   ```

Recuerda: Toda nueva implementación DEBE usar los modelos unificados en `database/narrative_unified.py`. NO crear nuevos modelos para narrativa sin consultar primero.