# Análisis del Menú de Administración

Este documento detalla la estructura y funcionalidad del panel de administración, basado en el análisis del código fuente.

## 1. Menú Principal de Administración (`/admin`)

El menú principal es el punto de entrada para todas las funciones administrativas. Se accede con el comando `/admin` y presenta las siguientes opciones:

- **💎 Canal VIP (`admin_vip`)**: Abre el menú de gestión del canal VIP.
- **💬 Canal Free (`admin_free`)**: Abre el menú de gestión del canal gratuito.
- **🎮 Juego Kinky (`admin_kinky_game`)**: Redirige al panel de gestión de Gamificación.
- **🛒 Tienda (`admin_shop`)**: Abre el menú de gestión de la tienda de productos.
- **📖 Narrativa (`admin_narrative_panel`)**: Abre el panel de administración de la narrativa.
- **💎 Mi Diván (`admin:midivan`)**: Abre la interfaz para gestionar los mensajes anónimos de los usuarios.
- **📊 Estadísticas (`admin_stats`)**: Muestra estadísticas generales del bot.
- **⚙️ Configuración (`admin_config`)**: Muestra el estado de la configuración del bot.
- **🔄 Actualizar (`admin_main_menu`)**: Recarga este menú.
- **↩️ Volver (`admin_back`)**: Navega al menú anterior.

## 2. Gestión de Canal VIP (`admin_vip`)

Este menú permite administrar el canal de suscriptores VIP.

- **📊 Estadísticas (`vip_stats`)**: Muestra estadísticas específicas del canal VIP.
- **🔑 Generar Token (`vip_generate_token`)**: Genera un token de invitación de un solo uso para el canal VIP.
- **👥 Suscriptores (`vip_manage`)**: Permite gestionar a los suscriptores del canal.
- **🏅 Asignar Insignia (`vip_manual_badge`)**: Permite asignar insignias manualmente a los usuarios VIP.
- **📝 Publicar Canal (`admin_send_channel_post`)**: Permite enviar una publicación al canal VIP.
- **⚙️ Configuración (`vip_config`)**: Abre la configuración específica del canal VIP.
- **💋 Config Reacciones (`vip_config_reactions`)**: Permite configurar las reacciones a los mensajes del canal.
- **🔄 Actualizar (`admin_vip_channel`)**: Recarga este menú.
- **↩️ Volver (`admin_main`)**: Vuelve al menú principal de administración.

## 3. Gestión de Canal Free (`admin_free`)

Este menú se utiliza para administrar el canal gratuito. Si el canal no está configurado, solo mostrará la opción para configurarlo.

- **⚙️ Configurar Canal (`configure_free_channel`)**: Inicia el proceso para configurar el canal gratuito.
- **⏰ Tiempo Espera (`set_wait_time`)**: Establece el tiempo que los usuarios deben esperar antes de ser aceptados en el canal.
- **🔗 Crear Enlace (`create_invite_link`)**: Crea un enlace de invitación para el canal.
- **📝 Enviar Contenido (`send_to_free_channel`)**: Permite enviar contenido al canal gratuito.
- **⚡ Procesar Ahora (`process_pending_now`)**: Procesa inmediatamente las solicitudes de unión pendientes.
- **🧹 Limpiar Antiguas (`cleanup_old_requests`)**: Elimina las solicitudes de unión antiguas.
- **📊 Estadísticas (`free_channel_stats`)**: Muestra estadísticas del canal gratuito.
- **💋 Config Reacciones (`free_config_reactions`)**: Permite configurar las reacciones a los mensajes del canal.
- **🔄 Actualizar (`admin_free_channel`)**: Recarga este menú.
- **↩️ Volver (`admin_main_menu`)**: Vuelve al menú principal de administración.

## 4. Gestión de Gamificación ("Juego Kinky") (`admin_kinky_game`)

Este panel centraliza la gestión de todos los aspectos relacionados con la ludificación.

- **👥 Usuarios (`admin_manage_users`)**: Gestiona los usuarios del sistema de gamificación.
- **🎯 Misiones (`admin_content_missions`)**: Administra las misiones disponibles para los usuarios.
- **🏅 Insignias (`admin_content_badges`)**: Administra las insignias que los usuarios pueden ganar.
- **📈 Niveles (`admin_content_levels`)**: Gestiona el sistema de niveles.
- **🎁 Catálogo VIP (`admin_content_rewards`)**: Administra las recompensas del catálogo VIP.
- **🏛️ Subastas (`admin_auction_main`)**: Gestiona el sistema de subastas.
- **🎁 Regalos Diarios (`admin_content_daily_gifts`)**: Configura los regalos diarios.
- **🕹 Minijuegos (`admin_content_minigames`)**: Administra los minijuegos.
- **🗺️ Pistas (`admin_content_lore_pieces`)**: Gestiona las pistas de la narrativa.
_ **🎉 Eventos (`admin_manage_events_sorteos`)**: Gestiona eventos y sorteos.
- **📦 CMS Journey (`cms_main`)**: Administra el contenido del "user journey".
- **🔄 Actualizar (`admin_manage_content`)**: Recarga este menú.
- **🏠 Panel Admin (`admin_main_menu`)**: Vuelve al menú principal de administración.

## 5. Gestión de la Tienda (`admin_shop`)

Permite la administración completa de los productos de la tienda.

- **📦 Ver Productos (`admin_shop_list`)**: Muestra una lista de todos los productos, permitiendo ver, editar o eliminar cada uno.
- **➕ Crear Producto (`admin_shop_create`)**: Inicia un asistente para crear un nuevo producto en la tienda.
- **🔗 Gestionar Desbloqueos (`admin_shop_unlocks`)**: Administra las condiciones que un usuario debe cumplir para desbloquear ciertos productos.
- **📊 Reportes de Ventas (`admin_shop_reports`)**: Muestra reportes de ventas de los productos.
- **🔙 Volver (`admin_main_menu`)**: Vuelve al menú principal de administración.

## 6. Panel de Narrativa (`admin_narrative_panel`)

Esta sección se encarga de la gestión de la historia interactiva del bot. Desde aquí se pueden visualizar, crear, editar y eliminar los diferentes componentes de la narrativa, como fragmentos de historia y las decisiones que los usuarios pueden tomar.

## 7. Mi Diván (`admin:midivan`)

Esta funcionalidad permite a los usuarios enviar mensajes anónimos al administrador. El panel de "Mi Diván" ofrece las siguientes opciones:

- **📬 Ver Mensajes**: Muestra una lista de los mensajes recibidos, indicando cuáles son nuevos. Permite ver el detalle de cada mensaje, responderlo o marcarlo para revisión.
- **📊 Estadísticas de Mensajes**: Muestra estadísticas sobre los mensajes recibidos y respondidos.
- **💘 Gestionar Quizzes**: Permite crear y administrar quizzes que pueden ser presentados a los usuarios.
- **📈 Estadísticas de Quizzes**: Muestra estadísticas sobre los quizzes.

## 8. Estadísticas (`admin_stats`)

Muestra una vista general de las estadísticas del bot, incluyendo:
- Número total de usuarios.
- Suscripciones totales, activas y expiradas.
- Ingresos totales.
- Estado de la configuración de los canales y tarifas.

## 9. Configuración (`admin_config`)

Presenta un resumen del estado de la configuración del bot, indicando si los canales, las tarifas y la gamificación han sido configurados correctamente.
