# Auditoría Técnica para MVP

Este documento detalla el análisis técnico del sistema narrativo actual y propone un plan de acción para la migración requerida para el MVP.

## 1. Análisis de la Deuda Técnica

El análisis del código revela una deuda técnica crítica centrada en la coexistencia de dos sistemas narrativos paralelos y conflictivos:

*   **Sistema Heredado:** Ubicado en `database/narrative_models.py`, se compone de múltiples tablas (`story_fragments`, `narrative_choices`, otro `narrative_fragments`, `narrative_decisions`) que representan al menos dos intentos de implementar una lógica narrativa. Este sistema es complejo, rígido y propenso a errores.
*   **Sistema Unificado:** Definido en `database/narrative_unified.py` y descrito en la documentación de arquitectura. Utiliza un diseño de un solo modelo (`NarrativeFragment`) que es flexible, robusto y escalable. Es el estándar a seguir.

**El `services/narrative_service.py` actual sigue utilizando el sistema heredado, ignorando el estándar de arquitectura y bloqueando el progreso.**

## 2. Plan de Migración Técnica

Se requiere un refactor completo para alinear la implementación con la arquitectura definida. El plan es el siguiente:

### Paso 1: Script de Migración de Datos

*   **Objetivo:** Mover todos los contenidos narrativos de las tablas antiguas a la nueva tabla `narrative_fragments_unified`.
*   **Acción:** Crear un script en `scripts/migrate_narrative_unified.py`.
*   **Lógica del Script:**
    1.  Leer todos los objetos de `StoryFragment` y `NarrativeFragment` (del modelo antiguo).
    2.  Para cada objeto, transformarlo en una instancia del nuevo `NarrativeFragment` unificado.
    3.  Mapear las antiguas `NarrativeChoice` y `NarrativeDecision` al campo JSON `choices` del nuevo modelo.
    4.  Mapear recompensas y condiciones a los campos JSON `triggers` y `required_clues`.
    5.  Insertar los nuevos objetos en la base de datos.
    6.  Migrar el progreso de los usuarios (`UserNarrativeState` antiguo al nuevo).

### Paso 2: Refactorización de Servicios

*   **Objetivo:** Eliminar toda dependencia del sistema narrativo antiguo.
*   **Acciones:**
    1.  **Crear `UnifiedNarrativeService`:** Crear un nuevo servicio en `services/unified_narrative_service.py` que implemente la lógica de negocio utilizando **exclusivamente** los modelos de `database/narrative_unified.py`.
    2.  **Eliminar `narrative_service.py`:** Una vez que el nuevo servicio esté funcional, eliminar el servicio antiguo.
    3.  **Actualizar Handlers:** Modificar todos los handlers que interactúan con la narrativa (ej. `handlers/narrative_handler.py`, `handlers/main_menu.py`) para que utilicen el nuevo `UnifiedNarrativeService`.

### Paso 3: Limpieza de Código

*   **Objetivo:** Erradicar completamente el código obsoleto.
*   **Acción:** Una vez que la migración de datos y la refactorización de servicios estén completadas y probadas, eliminar el archivo `database/narrative_models.py`.

## 3. Implementación de Funcionalidades del MVP

Una vez completada la migración, se podrán implementar las funcionalidades del MVP sobre una base sólida:

*   **Ciclo Narrativo:** Se implementará en el `UnifiedNarrativeService` y será consumido por el `narrative_handler`.
*   **Billetera:** Se creará un nuevo handler (`wallet_handler.py`) que consumirá la información del `point_service.py` para mostrar el balance de puntos.

Este plan resuelve la deuda técnica más crítica y desbloquea el desarrollo futuro del proyecto.
