# Sistema de Gestión de Solicitudes de Canal

## Descripción General

Este sistema gestiona las solicitudes de unión de usuarios a canales privados, especialmente el canal gratuito. Permite a los administradores revisar y aprobar estas solicitudes de manera centralizada, asegurando un control de acceso eficiente y una experiencia de usuario fluida.

## Arquitectura

### Componentes Principales

1.  **PendingChannelRequest (database/models.py)**
    -   Modelo de base de datos que almacena los detalles de cada solicitud de unión pendiente.
    -   Incluye `user_id`, `chat_id`, `request_timestamp`, `approved`, y `approval_timestamp`.

2.  **FreeChannelService (services/free_channel_service.py)**
    -   Servicio encargado de la lógica de negocio relacionada con el canal gratuito.
    -   Contiene el método `handle_join_request` que registra las solicitudes entrantes en la base de datos.

3.  **handlers/channel_access.py**
    -   Contiene el manejador `handle_join_request` que escucha los eventos `ChatJoinRequest` de Telegram.
    -   Delega el procesamiento inicial de la solicitud a `FreeChannelService`.
    -   El manejador `handle_chat_member` limpia las solicitudes pendientes una vez que el usuario se une o sale del canal.

4.  **handlers/admin.py**
    -   Módulo de administración que proporciona comandos para que los administradores gestionen las solicitudes.
    -   Incluye los comandos `/mostrar` para listar solicitudes pendientes y `/aceptar` para aprobarlas.

## Flujo de Trabajo

1.  **Solicitud de Unión**: Un usuario intenta unirse a un canal privado (ej. el canal gratuito) y envía una `ChatJoinRequest`.
2.  **Detección y Registro**: El manejador `handle_join_request` en `handlers/channel_access.py` intercepta la solicitud.
    -   Llama a `FreeChannelService.handle_join_request` para registrar la solicitud en la tabla `PendingChannelRequest` de la base de datos.
    -   Se envía una notificación al usuario informándole que su solicitud ha sido registrada y está pendiente de aprobación.
3.  **Revisión por Administrador**: Un administrador puede usar el comando `/mostrar` en el bot para ver una lista de todas las solicitudes pendientes, incluyendo el ID del usuario, el tiempo de espera y el ID del chat.
4.  **Aprobación por Administrador**: El administrador utiliza el comando `/aceptar`.
    -   El bot itera sobre todas las solicitudes pendientes marcadas como `approved=False`.
    -   Para cada solicitud, el bot llama a la API de Telegram (`bot.approve_chat_join_request`) para aprobar el acceso del usuario al canal.
    -   La solicitud se marca como `approved=True` en la base de datos y se registra la marca de tiempo de aprobación.
    -   Se notifica al usuario que su solicitud ha sido aprobada.
5.  **Limpieza de Solicitudes**: Una vez que el usuario se une al canal (detectado por `handle_chat_member`), la entrada correspondiente en `PendingChannelRequest` se elimina de la base de datos para mantenerla limpia.

## Comandos de Administración

Los administradores pueden usar los siguientes comandos para gestionar las solicitudes de canal:

-   `/mostrar`:
    -   **Descripción**: Muestra una lista de todas las solicitudes de unión a canales pendientes de aprobación.
    -   **Uso**: Simplemente envía `/mostrar` al bot.
    -   **Salida**: Una lista formateada con el ID del usuario, el tiempo transcurrido desde la solicitud y el ID del chat.

-   `/aceptar`:
    -   **Descripción**: Procesa y aprueba todas las solicitudes de unión a canales que están pendientes.
    -   **Uso**: Simplemente envía `/aceptar` al bot.
    -   **Salida**: Un mensaje de confirmación indicando cuántas solicitudes fueron procesadas y aprobadas.

## Integración

El sistema se integra con el flujo principal del bot a través de:

-   **bot.py**: El archivo principal del bot (`bot.py`) incluye el router de `handlers/channel_access.py`, asegurando que los eventos `ChatJoinRequest` y `ChatMemberUpdated` sean capturados y manejados correctamente.
-   **Base de Datos**: Utiliza el modelo `PendingChannelRequest` para la persistencia de datos de las solicitudes.
-   **Servicios**: Depende de `FreeChannelService` para la lógica de negocio y la interacción con la base de datos.
