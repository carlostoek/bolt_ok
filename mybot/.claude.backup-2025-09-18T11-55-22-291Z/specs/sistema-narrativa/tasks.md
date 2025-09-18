# Tareas de Implementación: Sistema de Narrativa

## Fase 1: Sistema de Administración de Narrativa (Backend)

### 1.1. Estructura de Archivos
- [ ] **Tarea 1.1.1:** Crear el archivo para el nuevo manejador de administración de narrativa en `handlers/admin/narrative_admin_handlers.py`.
- [ ] **Tarea 1.1.2:** Crear el archivo para el nuevo servicio de administración de narrativa en `services/admin/narrative_admin_service.py`.
- [ ] **Tarea 1.1.3:** Crear el archivo para los nuevos teclados de administración de narrativa en `keyboards/admin/narrative_admin_kb.py`.

### 1.2. Menú Principal de Administración
- [ ] **Tarea 1.2.1:** En `narrative_admin_handlers.py`, crear un manejador para el comando `/narrativa_admin` que muestre un menú principal.
- [ ] **Tarea 1.2.2:** En `narrative_admin_kb.py`, crear una función `get_main_admin_keyboard()` que genere un teclado con opciones para "Gestionar Fragmentos" y "Gestionar Decisiones".

### 1.3. Gestión de Fragmentos (CRUD)
- [ ] **Tarea 1.3.1:** En `narrative_admin_service.py`, implementar la función `get_all_fragments()` que devuelva todos los `StoryFragment` de la base de datos.
- [ ] **Tarea 1.3.2:** En `narrative_admin_handlers.py`, implementar un callback handler para "Gestionar Fragmentos" que use `get_all_fragments()` y muestre una lista paginada de fragmentos.
- [ ] **Tarea 1.3.3:** En `narrative_admin_service.py`, implementar la función `create_fragment(data)`.
- [ ] **Tarea 1.3.4:** En `narrative_admin_handlers.py`, implementar el flujo de FSM para crear un nuevo fragmento, pidiendo al administrador cada campo (`key`, `text`, etc.) por separado.
- [ ] **Tarea 1.3.5:** En `narrative_admin_service.py`, implementar `update_fragment(fragment_id, updates)` y `delete_fragment(fragment_id)`.
- [ ] **Tarea 1.3.6:** En `narrative_admin_handlers.py`, implementar los flujos para editar y eliminar fragmentos existentes.

### 1.4. Gestión de Decisiones (CRUD)
- [ ] **Tarea 1.4.1:** En `narrative_admin_service.py`, implementar `get_choices_for_fragment(fragment_id)`.
- [ ] **Tarea 1.4.2:** En `narrative_admin_handlers.py`, implementar un manejador para el comando `/narrativa_decisiones <fragment_key>` que muestre las decisiones del fragmento.
- [ ] **Tarea 1.4.3:** En `narrative_admin_service.py`, implementar `create_choice(fragment_id, data)`, `update_choice(choice_id, updates)`, y `delete_choice(choice_id)`.
- [ ] **Tarea 1.4.4:** En `narrative_admin_handlers.py`, implementar los flujos de FSM para crear, editar y eliminar decisiones de un fragmento.

## Fase 2: Mejoras de Experiencia de Usuario

### 2.1. Comando de Mochila/Inventario
- [ ] **Tarea 2.1.1:** Crear el archivo para el manejador de la mochila en `handlers/user/backpack_handler.py`.
- [ ] **Tarea 2.1.2:** Crear el archivo para el servicio de la mochila en `services/user/backpack_service.py`.
- [ ] **Tarea 2.1.3:** En `backpack_service.py`, implementar la función `get_user_narrative_items(user_id)` que consulta las compras del usuario y las filtra para obtener items narrativos.
- [ ] **Tarea 2.1.4:** En `backpack_handler.py`, implementar un manejador para el comando `/mochila` que use el servicio y muestre al usuario sus items.

## Fase 3: Lógica del Núcleo Narrativo

### 3.1. Flujo Condicionado por Items
- [ ] **Tarea 3.1.1:** Revisar `CoordinadorCentral._flujo_tomar_decision` para asegurar que la lógica de `decision_requirements` está completamente implementada como se describe en la guía.
- [ ] **Tarea 3.1.2:** Añadir tests unitarios para el `CoordinadorCentral` que verifiquen el flujo de decisiones condicionales (con y sin el item requerido).
- [ ] **Tarea 3.1.3:** Verificar que los fragmentos "teaser" (ej. `diana_diary_tease`) existen y se cargan correctamente.

### 3.2. Integración de Voz del Personaje
- [ ] **Tarea 3.2.1:** Revisar todos los mensajes orientados al usuario en los flujos narrativos (éxito, fallo, falta de puntos) y asegurarse de que utilizan el `CharacterVoiceService` para generar una respuesta consistente con la personalidad del personaje.
- [ ] **Tarea 3.2.2:** En `narrative_handlers.py`, en caso de que un requisito no se cumpla (puntos, rol), usar el `CharacterVoiceService` para generar el mensaje de error.
