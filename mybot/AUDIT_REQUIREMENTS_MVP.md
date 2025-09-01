# Auditoría de Requisitos para MVP

Este documento detalla las funcionalidades existentes del bot y define el alcance propuesto para un Producto Mínimo Viable (MVP) funcional.

## 1. Inventario de Funcionalidades Detallado

| Característica | Componentes Clave | Estado | Notas |
| :--- | :--- | :--- | :--- |
| **Gestión de Usuarios** | `handlers/start.py`, `services/user_service.py` | **Implementado** | Registro y actualización de usuarios al iniciar el bot. Diferencia entre roles de admin y usuario. |
| **Menú Principal** | `handlers/main_menu.py`, `constants/keyboards.py` | **Implementado** | Sistema de navegación principal funcional. |
| **Economía de Puntos** | `services/point_service.py` | **Implementado** | Sistema robusto para ganar puntos (mensajes, reacciones, check-in). Usa transacciones para auditoría. |
| **Niveles y Logros** | `services/level_service.py`, `services/achievement_service.py` | **Parcial** | Los servicios existen y están conectados al `point_service`, pero la interacción del usuario no es visible. |
| **Sistema Narrativo** | `services/narrative_service.py`, `docs/LECTURA_FORZOSA...` | **Conflicto** | Existe un servicio funcional (`narrative_service`) que usa un modelo de datos antiguo. La documentación exige un nuevo **Sistema Unificado** que no parece estar completamente integrado. |
| **Misiones** | `handlers/missions_handler.py` | **Parcial** | Existe un handler, pero la lógica completa del servicio no está clara. |
| **Billetera de Puntos** | `handlers/main_menu.py` | **No Implementado** | El botón del menú existe pero apunta a una funcionalidad "en desarrollo". |
| **Panel de Administración**| `handlers/admin/*` | **Implementado** | Extenso conjunto de herramientas para la gestión del bot. |

## 2. Propuesta de Alcance para MVP

El objetivo del MVP es ofrecer un ciclo de juego completo y coherente. La prioridad absoluta es resolver la inconsistencia del sistema narrativo.

| Funcionalidad MVP | Prioridad | Justificación |
| :--- | :--- | :--- |
| **1. Migración al Sistema Narrativo Unificado** | **CRÍTICA** | Es el núcleo de la experiencia. Se debe migrar la lógica actual para usar `database/narrative_unified.py` y refactorizar/crear un `UnifiedNarrativeService`. |
| **2. Ciclo Narrativo Básico** | **ALTA** | El usuario debe poder iniciar (`/start`), navegar por la historia (`📖 Historia`) y tomar decisiones que afecten su progreso. |
| **3. Ciclo de Puntos Básico** | **ALTA** | El usuario debe poder ganar puntos por interactuar (enviar mensajes) y ver su saldo total. |
| **4. Implementación de la "Billetera"** | **MEDIA** | Una pantalla simple que muestre al usuario su saldo de puntos actual. Es crucial para dar feedback al ciclo de gamificación. |

## 3. User Stories Clave del MVP

### US-01: Iniciar la Experiencia Narrativa

*   **Como** un nuevo usuario,
*   **Quiero** iniciar el bot con `/start`
*   **Para que** se cree mi perfil y se me presente el menú principal con la opción de empezar la historia.

**Criterios de Aceptación:**
*   Al usar `/start`, el usuario es guardado en la base de datos.
*   Se muestra un mensaje de bienvenida.
*   El menú principal incluye el botón "📖 Historia".

### US-02: Progresar en la Narrativa Unificada

*   **Como** un jugador,
*   **Quiero** interactuar con los fragmentos de la historia y tomar decisiones
*   **Para que** mi progreso se guarde y la historia avance.

**Criterios de Aceptación:**
*   Toda la lógica de la historia utiliza el `NarrativeFragment` del sistema unificado.
*   Las decisiones del usuario actualizan su `UserNarrativeState`.
*   El bot presenta el siguiente fragmento narrativo correctamente.

### US-03: Ganar Puntos por Interacción

*   **Como** un jugador,
*   **Quiero** ganar puntos al enviar mensajes
*   **Para que** se recompense mi participación.

**Criterios de Aceptación:**
*   Enviar un mensaje otorga una cantidad definida de puntos.
*   Existe un cooldown para evitar el spam de puntos.
*   La transacción de puntos queda registrada en el `PointTransaction`.

### US-04: Consultar Saldo de Puntos

*   **Como** un jugador,
*   **Quiero** usar el botón "💰 Billetera"
*   **Para que** pueda ver cuántos puntos tengo.

**Criterios de Aceptación:**
*   Al pulsar "💰 Billetera", el bot responde con el saldo actual de puntos del usuario.
*   El saldo mostrado coincide con el registro en la base de datos.
