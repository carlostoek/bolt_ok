# Plan de Acción para la Refactorización del Sistema Narrativo

Este documento detalla las acciones necesarias para unificar y robustecer el sistema de narrativa, dividido en fases priorizadas.

---

## Fase 1: Quick Wins (Estabilización Inmediata)

### 1.1. Centralizar Constantes (Eliminar "Magic Strings")
*   **Corrección:** Reemplazar strings hardcodeados (`"vip"`, `"adventurer"`, etc.) con referencias a Enums o clases de constantes para evitar errores de tipeo y facilitar el mantenimiento.
*   **Archivos Afectados Principalmente:**
    *   `database/narrative_models.py`
    *   `docs/NARRATIVE_FRAGMENTS_FORMAT.md` (actualizar documentación)
    *   `services/condition_checker.py`
    *   `handlers/narrative_handlers.py`
    *   `handlers/admin/shop_admin.py`
    *   `handlers/admin/game_admin.py`
    *   `scripts/setup_missions.py`
    *   `scripts/setup_shop.py`

### 1.2. Consolidar la Función `desbloquear_pista`
*   **Corrección:** Unificar las funciones duplicadas `desbloquear_pista` (en `narrativa.py`) y `desbloquear_pista_narrativa` (en `backpack.py`) en una única función canónica, preferiblemente dentro de un servicio dedicado.
*   **Archivos Afectados:**
    *   `narrativa.py` (candidato a eliminación)
    *   `backpack.py` (refactorizar o mover función)
    *   `services/lore_piece_service.py` (potencial destino para la función unificada)
    *   `combinar_pistas.py` (actualizar llamada)
    *   `handlers/admin/admin_menu.py` (actualizar llamada)

### 1.3. Resolver Dependencias Circulares en Handlers
*   **Corrección:** Eliminar los `import` locales dentro de las funciones en `handlers/narrative_handlers.py` mediante la reestructuración del orden de importación o moviendo las dependencias a un módulo de nivel inferior.
*   **Archivos Afectados:**
    *   `handlers/narrative_handlers.py`
    *   `modules/narrative/story_engine.py` (potencialmente necesita cambios para romper el ciclo)

---

## Fase 2: Refactorización Estratégica

### 2.1. Implementar Fachada `NarrativeService`
*   **Corrección:** Crear o consolidar un `NarrativeService` que actúe como el único punto de entrada para toda la lógica de narrativa (`StoryFragment` y `LorePiece`). Los módulos externos no deben acceder directamente a los modelos de la base de datos.
*   **Archivos Afectados (Lista Parcial):**
    *   `services/narrative_service.py` (crear/modificar)
    *   `services/shop_service.py`
    *   `services/mission_service.py`
    *   `services/level_service.py`
    *   `services/condition_checker.py`
    *   `handlers/shop_handlers.py`
    *   `handlers/lore_handlers.py`
    *   `handlers/admin/shop_admin.py`
    *   `handlers/admin/mission_wizard.py`
    *   *Nota: Afecta a más de 25 archivos. El objetivo es que todas las llamadas pasen por el nuevo servicio.*

---

## Fase 3: Evolución Arquitectónica

### 3.1. Unificar Modelos `LorePiece` y `StoryFragment`
*   **Corrección:** Migrar todos los datos y la lógica del sistema `LorePiece` al sistema `StoryFragment`. Esto requiere un script de migración de datos y la refactorización de toda la lógica que depende de `LorePiece` para que use `StoryFragment` exclusivamente a través del `NarrativeService`.
*   **Archivos Afectados:**
    *   **Fase de Scripting:**
        *   `scripts/migration/migrate_lore_to_fragments.py` (crear nuevo script)
    *   **Fase de Refactorización (vía `NarrativeService`):**
        *   `services/narrative_service.py` (modificar para usar solo `StoryFragment`)
    *   **Fase de Eliminación (Archivos a Eliminar/Modificar Drásticamente):**
        *   `database/models.py` (eliminar modelos `LorePiece`, `UserLorePiece`)
        *   `services/lore_piece_service.py` (eliminar archivo)
        *   `narrativa.py` (eliminar archivo)
        *   `handlers/lore_handlers.py` (eliminar/refactorizar)
        *   `handlers/admin/game_admin.py` (eliminar `LorePieceAdminStates` y su lógica)
        *   `states/gamification_states.py` (eliminar `LorePieceAdminStates`)
        *   `backpack.py` y `mochila.py` (eliminar toda la lógica de `LorePiece`)
        *   Todos los archivos restantes que importan o usan `LorePiece`.
