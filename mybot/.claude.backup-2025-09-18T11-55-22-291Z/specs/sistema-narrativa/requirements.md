# Requisitos para el Sistema de Narrativa

## 1. Introducción

El objetivo es diseñar, desarrollar e implementar el sistema de narrativa completo para el bot Diana. Este sistema debe ser inmersivo, adaptativo y estar profundamente integrado con los demás módulos del bot, como la gamificación (puntos/besitos) y la tienda (items).

Este documento se basa en el guión narrativo (`Narrativo.md`), la guía de implementación de fragmentos condicionados por items, y el código existente.

## 2. Requisitos Funcionales

### RF-01: Motor de Narrativa Principal

- **User Story:** Como jugador, quiero experimentar una historia interactiva y ramificada, para poder sumergirme en el mundo de Diana y sentir que mis decisiones tienen un impacto.
- **Acceptance Criteria:**
    - WHEN elijo una opción en un fragmento narrativo, THEN soy presentado con el siguiente fragmento correspondiente a mi elección.
    - WHEN un fragmento tiene recompensas (puntos), THEN los puntos se añaden a mi total.
    - WHEN un fragmento desbloquea un logro, THEN el logro se me otorga.
    - WHEN un fragmento no tiene opciones, THEN avanzo automáticamente al siguiente fragmento si está definido.

### RF-02: Contenido Narrativo Condicionado

- **User Story:** Como jugador, quiero poder desbloquear arcos narrativos especiales usando items que compro en la tienda, para sentir que mis compras tienen un valor más allá de la simple posesión.
- **Acceptance Criteria:**
    - GIVEN que una decisión narrativa requiere un item que no poseo, WHEN intento tomar esa decisión, THEN se me presenta un fragmento "teaser" que me informa del requisito y me guía hacia la tienda.
    - GIVEN que poseo el item requerido para una decisión, WHEN tomo esa decisión, THEN accedo al fragmento de contenido exclusivo.
    - WHEN compro un item que desbloquea contenido narrativo, THEN el item aparece en mi inventario/mochila.

### RF-03: Sistema de Administración de Narrativa (Admin Panel)

- **User Story:** Como administrador del bot, necesito una interfaz para gestionar todo el contenido narrativo, para poder crear, modificar y eliminar arcos de la historia sin necesidad de tocar el código o la base de datos directamente.
- **Acceptance Criteria:**
    - **Gestión de Fragmentos:**
        - WHEN accedo al panel de administración, THEN puedo ver una lista de todos los `StoryFragment`s.
        - WHEN selecciono la opción de crear, THEN puedo definir un nuevo fragmento con su `key`, texto, personaje, nivel y condiciones (puntos, rol requerido).
        - WHEN edito un fragmento, THEN puedo modificar todos sus campos.
        - WHEN elimino un fragmento, THEN se elimina de la base de datos (con las debidas confirmaciones y advertencias sobre enlaces rotos).
    - **Gestión de Decisiones:**
        - WHEN veo un fragmento, THEN puedo ver, añadir, editar o eliminar las `NarrativeChoice`s asociadas.
        - WHEN creo o edito una decisión, THEN puedo definir su texto y el `key` del fragmento de destino.
        - WHEN creo o edito una decisión, THEN puedo definir condiciones para ella (puntos, rol, item requerido).
    - **Visualizador de Flujo (Opcional, pero deseable):**
        - WHEN estoy en el panel de administración, THEN puedo ver una representación gráfica del flujo narrativo, mostrando cómo se conectan los fragmentos.

### RF-04: Experiencia de Usuario Mejorada

- **User Story:** Como jugador, quiero una experiencia fluida y clara al interactuar con la narrativa y los sistemas conectados, para no sentirme perdido o frustrado.
- **Acceptance Criteria:**
    - WHEN no tengo suficientes puntos para una decisión, THEN recibo un mensaje claro y con la voz del personaje apropiado (ej. Diana, Lucien) explicándome cómo conseguir más.
    - WHEN accedo a mi perfil o inventario, THEN puedo ver los items especiales que he adquirido y que desbloquean narrativa.
    - WHEN la narrativa se actualiza o se añaden nuevos arcos, THEN (opcionalmente) puedo recibir una notificación si estoy suscrito a ellas.
    - WHEN interactúo con el bot, THEN las respuestas de los personajes (Diana, Lucien) son consistentes con su personalidad definida en `Narrativo.md` y el contexto emocional.

## 3. Requisitos No Funcionales

- **RNF-01: Escalabilidad:** El sistema debe ser capaz de soportar una historia con cientos de fragmentos y decisiones sin degradación del rendimiento.
- **RNF-02: Modularidad:** La lógica de la narrativa debe estar bien encapsulada para facilitar la integración con futuros módulos. La `CoordinadorCentral` ya establece un buen patrón para esto.
- **RNF-03: Persistencia:** El estado narrativo de cada usuario debe guardarse de forma persistente en la base de datos.
- **RNF-04: Testeabilidad:** Los servicios y componentes del sistema narrativo deben ser unitariamente testeables.

## 4. Fuera de Alcance (Para esta iteración)

-   Traducción de la narrativa a otros idiomas.
-   Generación de contenido narrativo por IA en tiempo real.
-   Un sistema de misiones completamente dinámico fuera del flujo narrativo principal.
