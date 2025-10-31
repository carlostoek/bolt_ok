# Análisis de Flujos de Conexión del Bot

Este documento detalla los flujos de conexión entre los diferentes módulos del sistema del bot, basándose exclusivamente en el análisis del código fuente. La base de datos actúa como el sistema nervioso central que conecta todos los módulos.

## 1. Desbloqueo de Niveles Narrativos

El progreso narrativo no es lineal y se desbloquea a través de una combinación de decisiones del usuario, su estado y los objetos que posee.

- **Estructura Principal**: La narrativa se compone de `StoryFragment` (fragmentos de historia) conectados por `NarrativeChoice` (decisiones). El progreso de cada usuario se guarda en la tabla `UserNarrativeState`, que registra su `current_fragment_key`.

- **Flujo de Desbloqueo por Decisión**:
    1.  El usuario, находясь en un `StoryFragment`, recibe varias `NarrativeChoice`.
    2.  Al seleccionar una, el `narrative_handler` llama al `NarrativeService`.
    3.  El `NarrativeService` ejecuta la función `_check_decision_requirements`. Esta función comprueba si el usuario cumple con las condiciones almacenadas en la propia `NarrativeChoice` en la base de datos:
        - `required_besitos`: Si el usuario tiene suficientes puntos (ej. `user.points >= choice.required_besitos`).
        - `required_role`: Si el usuario tiene el rol necesario (ej. "vip").
    4.  Si se cumplen los requisitos, se actualiza el `current_fragment_key` del usuario en `UserNarrativeState` al `destination_fragment_key` de la decisión elegida, moviendo así al usuario al siguiente punto de la historia.

- **Desbloqueo por Arquetipo**: El `NarrativeService` analiza las decisiones pasadas del usuario (`choices_made`) para asignarle un arquetipo (ej. "aventurero"). Al solicitar un fragmento, el sistema busca primero una versión específica para ese arquetipo (ej. `clave_fragmento_aventurero`) antes de recurrir a la versión genérica, personalizando la experiencia.

## 2. Impacto de la Compra de Objetos en la Tienda

La tienda (`Shop`) es un motor clave para la progresión y la gamificación, con conexiones directas y potentes a la narrativa.

- **Flujo de Compra**:
    1.  El `shop_handlers` gestiona la interacción del usuario con la tienda.
    2.  Al intentar comprar un `ShopItem`, se llama al método `purchase_item` en `ShopService`.
    3.  Este método realiza varias comprobaciones: si el usuario tiene suficientes puntos (`user.points`), si el objeto está en stock, si el usuario ya ha alcanzado el límite de compra, etc.

- **Conexión Directa con la Narrativa**: El modelo `ShopItem` contiene dos campos cruciales que lo conectan directamente con la narrativa:
    1.  `unlocks_lore_piece_id`: Si este campo tiene un valor, la compra exitosa crea una entrada en la tabla `UserLorePiece`, otorgando al usuario una "pista" o pieza de historia que puede consultar en su "mochila".
    2.  `unlocks_fragment_key`: Este es el vínculo más fuerte. Si este campo tiene un valor, el `ShopService` llama directamente al `NarrativeService` (`narrative_service.navigate_to_fragment`). Esto **cambia forzosamente el `current_fragment_key` del usuario**, teletransportándolo a un nuevo punto de la historia que antes era inaccesible.

- **Requisitos de Desbloqueo Complejos**:
    - Los `ShopItem` tienen un campo JSON llamado `unlock_requirements`.
    - El `ShopService` utiliza un `ConditionChecker` que interpreta este JSON. Esto permite que los objetos de la tienda solo estén disponibles si el usuario cumple condiciones complejas, como "haber completado la misión X" o "poseer el objeto Y".

## 3. Conexión entre Gamificación y Administración

La "gamificación" (misiones, puntos, logros) y el módulo de administración están conectados a través de la base de datos. El módulo de administración actúa como un panel de control que modifica el estado del juego de un usuario.

- **La Moneda del Juego**: Los "besitos" (`user.points`) son la moneda central. El usuario los gana a través de actividades de gamificación (completar `Mission`, obtener `Achievement`, etc.) y los gasta en la tienda.

- **Flujo de Interacción del Administrador**:
    1.  Un usuario con `is_admin = True` accede a comandos especiales gestionados por los `handlers/admin/*.py`.
    2.  Estos manejadores permiten al administrador interactuar con los servicios o directamente con los repositorios de la base de datos.
    3.  **Ejemplos de Conexión**:
        - **Manipulación de Puntos**: Un administrador puede añadir o quitar "besitos" a un usuario, afectando directamente su capacidad para tomar decisiones narrativas o comprar objetos.
        - **Otorgar Objetos/Logros**: Un administrador puede crear entradas directamente en las tablas `UserPurchase` o `UserAchievement`, dando a un usuario acceso a objetos o logros que normalmente requerirían esfuerzo. Esto, a su vez, puede desbloquear nuevos caminos narrativos o artículos en la tienda.
        - **Gestión de la Tienda**: El `shop_admin.py` permite a los administradores crear y modificar `ShopItem`, incluyendo la definición de sus `price` y sus `unlock_requirements`, controlando así la economía y el flujo de desbloqueo del juego.

## 4. Conexiones entre Narrativa y Administración

La conexión es similar a la de la gamificación: los administradores tienen control total sobre el estado narrativo de cualquier usuario a través de la manipulación de la base de datos.

- **Control del Progreso Narrativo**:
    - A través de `handlers/admin/narrative_admin.py`, un administrador puede leer el estado de `UserNarrativeState` de un usuario.
    - Puede ver el `current_fragment_key` del usuario, su historial de decisiones (`choices_made`) y los fragmentos que ha desbloqueado (`unlocked_fragments`).
    - Más importante aún, un administrador puede **modificar** el `current_fragment_key` de un usuario, moviéndolo a cualquier punto de la historia, saltándose requisitos o repitiendo eventos.

- **Edición de la Narrativa**: Los administradores pueden usar sus herramientas para editar directamente las tablas `StoryFragment` y `NarrativeChoice`, cambiando textos, requisitos de "besitos", o el destino de una decisión, alterando la estructura de la historia para todos los usuarios en tiempo real.

En resumen, el sistema está diseñado con una clara separación de preocupaciones (servicios, manejadores, modelos), pero todos los módulos convergen y se comunican modificando y reaccionando a un estado compartido y persistente en la base de datos. El módulo de administración funciona como una interfaz de "superusuario" para leer y escribir directamente en este estado central.
