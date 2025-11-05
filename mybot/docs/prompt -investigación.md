**Prompt para Investigación Profunda: Diseño e Implementación de una Interfaz de Configuración Unificada para DianaBot**

**Contexto Actual:**
El sistema DianaBot cuenta con una implementación robusta y avanzada en sus módulos principales: Narrativa Inmersiva, Gamificación y Administración de Canales. La interconexión entre estos módulos es fuerte y funcional. Sin embargo, la gestión administrativa de estos módulos se realiza actualmente a través de una serie de menús y manejadores fragmentados dentro del bot de Telegram (ej. `handlers/admin/`, `keyboards/admin_*.py`). Esto dificulta la configuración de elementos interdependientes (como recompensas narrativas, desbloqueos de tienda, condiciones de misiones, etc.) desde un único punto de control, requiriendo la navegación entre múltiples secciones.

**Objetivo de la Investigación:**
Diseñar una propuesta detallada para una **Interfaz de Configuración Unificada** que permita a los administradores gestionar de manera intuitiva y eficiente todos los aspectos interconectados de DianaBot desde un solo lugar, mejorando la experiencia de usuario del administrador y la coherencia en la configuración del contenido.

**Preguntas Clave a Responder y Áreas a Explorar:**

1.  **Análisis de Requisitos y Flujos de Trabajo del Administrador:**
    *   Identificar los flujos de trabajo más comunes que un administrador realizaría al configurar contenido interconectado (ej. crear un fragmento narrativo con una recompensa de "besitos" y una condición de desbloqueo por un ítem de la tienda, o una misión que desbloquea un logro y un fragmento VIP).
    *   ¿Qué entidades (fragmentos, ítems de tienda, misiones, logros, roles, suscripciones) necesitan ser configuradas conjuntamente o tener referencias cruzadas en una única vista?
    *   ¿Cuáles son los puntos de dolor actuales para los administradores debido a la fragmentación de la interfaz?

2.  **Opciones de Implementación de la Interfaz:**
    *   **Interfaz Web (Recomendado):**
        *   Investigar frameworks web ligeros y adecuados para Python (ej. Flask, FastAPI con un frontend simple como Jinja2, React/Vue si se justifica la complejidad).
        *   Proponer una arquitectura de alto nivel para la aplicación web (ej. cómo se conectaría con la base de datos existente, autenticación de administradores, etc.).
        *   Identificar las bibliotecas o herramientas necesarias para la creación de formularios dinámicos y la gestión de relaciones complejas (ej. selección de fragmentos para desbloqueo, asignación de recompensas).
    *   **Interfaz Avanzada en Telegram (Alternativa):**
        *   Si una interfaz web no es viable, ¿cómo se podría consolidar la experiencia administrativa dentro de Telegram? Esto implicaría el uso intensivo de mensajes editables, teclados inline dinámicos y posiblemente un sistema de "pasos" o "wizard" para la configuración de elementos complejos.
        *   ¿Qué limitaciones impone Telegram para lograr una verdadera "unificación" en comparación con una interfaz web?

3.  **Diseño de la Experiencia de Usuario (UX) y la Interfaz de Usuario (UI):**
    *   Proponer un diseño conceptual para las vistas clave de la interfaz unificada (ej. una vista de edición de fragmento narrativo que incluya campos para texto, imagen, personaje, nivel, `min_besitos`, `reward_besitos`, `unlocks_achievement_id`, y una sección para definir las `choices` con sus `required_besitos` y `required_role`, y quizás un selector de ítems de tienda que desbloquean este fragmento).
    *   Considerar cómo se visualizarían y editarían las relaciones entre entidades (ej. un selector de "logro a desbloquear" que muestre los logros existentes).
    *   ¿Cómo se manejaría la previsualización del contenido o los efectos de una configuración antes de guardarla?

4.  **Impacto en el Código Base Existente:**
    *   Identificar qué manejadores (`handlers/admin/`), servicios (`services/`), modelos (`database/`) y teclados (`keyboards/`) existentes necesitarían ser refactorizados, modificados o eliminados para dar paso a la nueva interfaz.
    *   ¿Cómo se integrarían los nuevos componentes de la interfaz con la lógica de negocio actual sin introducir regresiones?
    *   ¿Se necesitarían nuevos modelos de base de datos o modificaciones a los existentes para soportar la configuración unificada?

5.  **Plan de Desarrollo de Alto Nivel:**
    *   Esbozar los pasos principales para la implementación de esta interfaz, desde el diseño inicial hasta la integración y pruebas.
    *   Identificar posibles hitos y dependencias.

**Formato de la Respuesta:**
La respuesta debe ser un documento estructurado en Markdown, abordando cada uno de los puntos anteriores con propuestas concretas, justificaciones y, si es posible, ejemplos de cómo se vería la interacción o la estructura de datos.

---