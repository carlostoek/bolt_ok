# Roadmap de Implementación del MVP

**Versión:** 1.0
**Fecha:** 2025-08-29

## 1. Visión del Producto Mínimo Viable (MVP)

El objetivo de este MVP no es solo entregar un conjunto de características, sino establecer una **base técnica y narrativa estable** que permita un crecimiento futuro sostenible. El entregable final será una experiencia de usuario coherente y emocionalmente atractiva, centrada en un ciclo de interacción principal: **participar en la historia, sentir el progreso a través de puntos y ver un reflejo de esa inversión.**

Este roadmap es el resultado de una auditoría exhaustiva realizada por los agentes `@requirements-analyst`, `@backend-developer` y `@narrative-designer`.

## 2. Componentes Principales del MVP

| # | Componente | Descripción | Requisito Clave |
|---|---|---|---|
| 1 | **Núcleo Narrativo Unificado** | Migración completa del sistema a los modelos de `narrative_unified.py`. | **Técnico:** Implementar el plan de migración. **Narrativo:** Asegurar que la voz del personaje se mantenga según las directrices. |
| 2 | **Ciclo de Historia Principal** | Flujo completo para que el usuario inicie y progrese en la narrativa. | **Funcional:** El usuario puede tomar decisiones que afectan su progreso. |
| 3 | **Ciclo de Puntos (Interés)** | El usuario gana puntos por interactuar con la historia. | **Narrativo:** Los puntos se enmarcan como "interés" o "influencia" sobre Diana. |
| 4 | **Reflejo del Interés (Billetera)** | Una interfaz para que el usuario vea su progreso (puntos). | **Narrativo:** La presentación del saldo debe tener un envoltorio narrativo. |

## 3. Roadmap de Implementación por Fases

### Fase 1: Migración del Núcleo (Prioridad CRÍTICA)

*   **Tarea 1.1: Crear Script de Migración.**
    *   **Descripción:** Desarrollar el script `scripts/migrate_narrative_unified.py` según la auditoría técnica.
    *   **Agente Responsable:** `@backend-developer`

*   **Tarea 1.2: Ejecutar y Validar Migración de Datos.**
    *   **Descripción:** Ejecutar el script en un entorno de prueba y validar que todo el contenido y progreso de los usuarios se ha migrado sin pérdidas.
    *   **Agente Responsable:** `@backend-developer`

*   **Tarea 1.3: Refactorizar Servicios y Handlers.**
    *   **Descripción:** Crear `UnifiedNarrativeService`, eliminar el servicio antiguo y actualizar todos los handlers para que usen el nuevo servicio.
    *   **Agente Responsable:** `@backend-developer`

*   **Tarea 1.4: Validar Integridad Narrativa Post-Migración.**
    *   **Descripción:** Revisar una muestra del contenido migrado para asegurar que las directrices de la auditoría narrativa se han cumplido.
    *   **Agente Responsable:** `@narrative-designer`

### Fase 2: Implementación de Features

*   **Tarea 2.1: Implementar Handler de Billetera.**
    *   **Descripción:** Crear el handler para el botón "💰 Billetera" que muestre el saldo de puntos.
    *   **Agente Responsable:** `@backend-developer`

*   **Tarea 2.2: Aplicar Envoltorio Narrativo a la Billetera.**
    *   **Descripción:** Asegurar que el texto de la billetera cumpla con las directrices de la auditoría narrativa.
    *   **Agente Responsable:** `@narrative-designer`

### Fase 3: Pruebas y Cierre

*   **Tarea 3.1: Pruebas E2E del Flujo del MVP.**
    *   **Descripción:** Realizar una prueba completa del ciclo: iniciar, jugar, ganar puntos, ver billetera.
    *   **Agente Responsable:** `@debug-specialist` (o PM)

*   **Tarea 3.2: Limpieza Final del Código.**
    *   **Descripción:** Eliminar el archivo `database/narrative_models.py` una vez que todas las pruebas pasen.
    *   **Agente Responsable:** `@backend-developer`

## 4. Riesgos y Mitigaciones

| Riesgo | Mitigación |
|---|---|
| La migración de datos es más compleja de lo esperado. | El script de migración debe ser exhaustivamente probado en un entorno de staging antes de aplicarse a producción. |
| La voz del personaje se diluye en la nueva implementación. | El `@narrative-designer` debe aprobar todas las cadenas de texto de cara al usuario y revisar la implementación de los fragmentos narrativos clave. |

## 5. Próximos Pasos

Este roadmap ahora sirve como el plan de acción oficial. El siguiente paso es comenzar la ejecución de la **Fase 1**.
