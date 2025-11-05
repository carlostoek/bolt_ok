# Mapa del Módulo de Narrativa

Este documento describe el flujo de archivos y funciones para el módulo de narrativa, separado por el flujo de Administrador y el de Usuario Normal.

## Flujo de Administrador

El flujo de administrador comienza en el panel de control principal del bot.

1.  **Inicio**: `keyboards/admin_main_kb.py`
    *   El administrador pulsa el botón "📖 Narrativa".
    *   `callback_data="admin_narrative_panel"`

2.  **Panel Principal de Narrativa**: `handlers/admin/narrative_admin.py`
    *   La función `show_narrative_admin_panel` maneja el callback.
    *   Muestra un menú con las siguientes opciones:

        *   **"📚 Gestionar Fragmentos"**:
            *   `callback_data="narrative_admin_fragments"`
            *   Llama a `show_fragments_management` en el mismo archivo.
            *   Desde aquí, se pueden crear, ver, editar y eliminar fragmentos, todo gestionado dentro de `handlers/admin/narrative_admin.py`.

        *   **"🔀 Gestionar Decisiones"**:
            *   `callback_data="narrative_admin_choices"`
            *   **FUNCIONALIDAD NO IMPLEMENTADA.**

        *   **"📥 Cargar desde Directorio"**:
            *   `callback_data="narrative_admin_load_directory"`
            *   Llama a `load_narrative_from_directory` en el mismo archivo.
            *   Esta función utiliza `services/narrative_loader.py` para cargar los fragmentos desde el directorio `mybot/narrative_fragments`.

        *   **"📤 Subir Archivo JSON"**:
            *   `callback_data="narrative_admin_upload"`
            *   Llama a `upload_narrative_file` en el mismo archivo, que espera un archivo JSON.
            *   El archivo es procesado por `handle_narrative_file`, que también utiliza `services/narrative_loader.py`.

        *   **"🔗 Vincular Productos"**:
            *   `callback_data="narrative_admin_link_products"`
            *   Llama a `show_product_linking` (actualmente un placeholder).

        *   **"✅ Validar Narrativa"**:
            *   `callback_data="narrative_admin_validate"`
            *   Llama a `validate_narrative` para comprobar la integridad de la historia.

        *   **"📊 Estadísticas Detalladas"**:
            *   `callback_data="narrative_admin_stats"`
            *   Llama a `show_detailed_stats`.

## Flujo de Usuario Normal

El flujo de usuario normal comienza desde el menú principal del bot.

1.  **Inicio**: `keyboards/main_menu_kb.py` (o `keyboards/subscription_kb.py`)
    *   El usuario pulsa el botón "📖 Historia".
    *   `callback_data="start_narrative"`

2.  **Manejador de Inicio de Narrativa**: `handlers/narrative_handler.py`
    *   La función `start_narrative_callback` maneja el callback y llama a `start_narrative_command`.
    *   `start_narrative_command` utiliza `services/narrative_service.py` para obtener el fragmento de historia inicial (`start`).

3.  **Servicio de Narrativa**: `services/narrative_service.py`
    *   La función `start_narrative` obtiene el estado del usuario y el `StoryFragment` inicial de la base de datos (definido en `database/narrative_models.py`).

4.  **Visualización del Fragmento**: `handlers/narrative_handler.py`
    *   La función `_display_narrative_fragment` muestra el texto del fragmento y un teclado.
    *   El teclado se genera con `keyboards/narrative_kb.py`.

5.  **Interacción del Usuario**: `keyboards/narrative_kb.py`
    *   El usuario pulsa un botón de decisión en el teclado.
    *   `callback_data="narrative_choice:{index}"`

6.  **Manejador de Decisiones**: `handlers/narrative_handler.py`
    *   La función `handle_narrative_choice` procesa la elección del usuario.
    *   Utiliza `services/narrative_service.py` para:
        *   Verificar si el usuario cumple los requisitos de la decisión.
        *   Obtener el siguiente `StoryFragment`.
        *   Actualizar el estado del usuario en la base de datos.
    *   El ciclo se repite desde el paso 4.

### Otros Flujos de Usuario

*   **Continuar Historia**:
    *   Botón: "📖 Continuar historia" en `keyboards/besitos_kb.py`.
    *   `callback_data="continue_narrative_after_purchase"` o `continue_narrative`.
    *   Manejado en `handlers/narrative_handler.py` por `continue_narrative`.
*   **Ver Estadísticas**:
    *   Comando: `/mi_historia`.
    *   Manejado por `show_narrative_stats` en `handlers/narrative_handler.py`.
