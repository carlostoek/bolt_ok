# MANUAL TÉCNICO: Revisión y Solución de Problemas del MVP de Narrativa

Este documento detalla los hallazgos, las acciones tomadas y los próximos pasos planificados durante la sesión de depuración del bot, centrándose en el sistema de narrativa MVP.

## 1. Problema Inicial

El bot presentaba una serie de errores críticos que impedían el correcto funcionamiento del sistema de narrativa MVP, afectando la progresión del usuario, la gestión de arquetipos y la visualización de menús.

## 2. Hallazgos y Análisis Detallado

Se identificaron varios problemas principales, categorizados a continuación:

### 2.1. Problemas de Base de Datos (Tablas Faltantes)

*   **Error:** `sqlite3.OperationalError: no such table: user_mission_progress_unified`
*   **Error:** `sqlite3.OperationalError: no such table: user_archetypes_unified`
*   **Análisis:** Estos errores indicaban que las tablas `user_mission_progress_unified` y `user_archetypes_unified`, fundamentales para el seguimiento del progreso del usuario y la clasificación de arquetipos en el nuevo sistema unificado, no existían en la base de datos. Esto causaba fallos en cascada en múltiples servicios que dependían de ellas.
*   **Hallazgo Adicional:** La tabla `narrative_fragments_unified` también estaba vacía, lo que provocaba errores de "Fragment not found" al intentar iniciar o continuar la narrativa.

### 2.2. Error de Instanciación de Pydantic `BaseModel`

*   **Error:** `BaseModel.__init__() takes 1 positional argument but 2 were given`
*   **Ubicación:** Este error se manifestaba en `services/enhanced_diana_menu_system.py`, específicamente dentro de las funciones `_handle_besitos_menu`, `_handle_missions_menu` y `_create_narrative_keyboard`.
*   **Análisis:** Este es un error común en Pydantic v2 cuando un modelo se intenta instanciar con argumentos posicionales en lugar de argumentos de palabra clave. A pesar de que el código parecía pasar argumentos de palabra clave a `InlineKeyboardButton` (una clase de `aiogram` que internamente usa Pydantic), el error sugería una mala interpretación de los argumentos. El error era intermitente y reaparecía después de reinicios de la base de datos.

### 2.3. Problemas de Carga de Fragmentos Narrativos

*   **Error:** `Level 1 Fragment 1 not found` y `Starting fragment 'diana_l1_f1_umbral' not found`.
*   **Análisis:** Se descubrió que el servicio `services/narrative_loader.py` estaba diseñado para cargar fragmentos en tablas *antiguas y deprecadas* (`StoryFragment`, `NarrativeChoice`) en lugar de la tabla unificada `narrative_fragments_unified`. Esto significaba que, aunque la tabla `narrative_fragments_unified` existiera, permanecía vacía, impidiendo el inicio de la narrativa. El servicio `MVPNarrativeFragmentService` contenía la lógica correcta para inicializar los fragmentos MVP en la tabla unificada, pero no estaba siendo invocado.

### 2.4. Error de Transacción de SQLAlchemy

*   **Error:** `IllegalStateChangeError: Method 'close()' can't be called here; method '_connection_for_bind()' is already in progress and this would cause an unexpected state change`.
*   **Ubicación:** Este error se produjo en `bot.py` dentro del `DBSessionMiddleware`, específicamente durante el intento de `session.close()`.
*   **Análisis:** La causa fue un conflicto entre el inicio de una transacción implícita por SQLAlchemy (debido al comportamiento "begin-on-first-use" del `DBSessionMiddleware`) y un intento explícito de iniciar otra transacción (`async with self.session.begin():`) dentro de la función `transition_user_role` en `services/enhanced_user_service.py`. El cierre explícito de la sesión en el `finally` del middleware también contribuía al problema al intentar cerrar una conexión que ya estaba en un estado de cambio.

## 3. Acciones Tomadas

Se implementaron las siguientes soluciones para abordar los problemas identificados:

*   **Creación Automática de Tablas de Base de Datos:**
    *   Se integró la función `create_missing_tables_sync()` de `create_missing_tables.py` en la función `main()` de `bot.py`. Esta función ahora se ejecuta al inicio del bot, asegurando que las tablas `user_mission_progress_unified`, `user_archetypes_unified` y `narrative_fragments_unified` se creen automáticamente si no existen.
*   **Inicialización de Fragmentos Narrativos MVP:**
    *   Se modificó `bot.py` para importar `MVPNarrativeFragmentService` y se añadió una llamada a `mvp_fragment_service.initialize_mvp_fragments()` dentro de `main()`, justo después de la inicialización de la base de datos. Esto garantiza que los fragmentos narrativos del MVP se carguen correctamente en la tabla `narrative_fragments_unified` al iniciar el bot.
*   **Corrección del Error de Transacción de SQLAlchemy:**
    *   Se eliminó el bloque `async with self.session.begin():` de la función `transition_user_role` en `services/enhanced_user_service.py`. La transacción ahora es manejada implícitamente por el `DBSessionMiddleware`, y el `await self.session.commit()` existente es suficiente para confirmar los cambios.
    *   Se eliminó el `await session.close()` del bloque `finally` en el `DBSessionMiddleware` en `bot.py`, ya que el `async with self.session_pool()` ya gestiona el ciclo de vida de la sesión, evitando el `IllegalStateChangeError`.
*   **Depuración del Error de Instanciación de Pydantic `BaseModel` (Parcial):**
    *   Se añadió una declaración `logger.debug` en `services/enhanced_diana_menu_system.py` (línea 1621) para inspeccionar los valores de `text` y `callback_data` justo antes de la creación de `InlineKeyboardButton`. Esto se hizo para obtener más información sobre el tipo y el contenido de los argumentos que estaban causando el error.

## 4. Próximos Pasos (Lo que se iba a hacer)

Antes de finalizar la sesión, se tenía previsto continuar con los siguientes pasos:

*   **Análisis de Logs para el Error `BaseModel.__init__()`:**
    *   Analizar la salida de los logs generados por la declaración `logger.debug` añadida en `services/enhanced_diana_menu_system.py`. El objetivo era identificar si `choice['text']` o `choice['callback_data']` no eran cadenas de texto (strings) o si se estaban pasando de una manera inesperada a `InlineKeyboardButton`, lo que podría estar causando el error de Pydantic.
    *   Basándose en la información de los logs, se determinaría la causa raíz exacta del error.
*   **Implementación de la Solución para `BaseModel.__init__()`:**
    *   Una vez identificada la causa, se implementaría una solución para asegurar que `InlineKeyboardButton` reciba argumentos válidos (cadenas de texto) para `text` y `callback_data`. Esto podría implicar la conversión explícita de tipos o la modificación de la fuente de datos para garantizar la consistencia.
*   **Pruebas Exhaustivas del Sistema de Narrativa:**
    *   Después de resolver el error de `BaseModel`, se realizarían pruebas exhaustivas de todo el sistema de narrativa. Esto incluiría la verificación de todas las interacciones del menú, la progresión narrativa, las transiciones de roles de usuario, la correcta asignación de puntos y el seguimiento de logros.
    *   Se prestaría especial atención a la validación de la consistencia del personaje de Diana y a las métricas de rendimiento para asegurar que el sistema cumple con los requisitos de MVP.

Este manual técnico sirve como un registro de los problemas encontrados y las acciones tomadas, facilitando la continuación del trabajo en el futuro.
