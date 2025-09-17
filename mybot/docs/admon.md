### Sistema de Administración de Canales – DianaBot

El **Sistema de Administración de Canales** de DianaBot es el pilar operativo que garantiza el control, la seguridad, la monetización y la gestión eficiente de los canales gratuito y VIP en los que opera el bot. Este módulo se encarga de regular el acceso de usuarios, gestionar suscripciones, programar y proteger contenido, y ofrecer herramientas administrativas avanzadas para personalizar la experiencia. A continuación, se detalla exhaustivamente sus funciones, acciones, conexiones con otros módulos y su relevancia dentro del ecosistema.

---

### **Propósito y Visión General**
El módulo de administración de canales actúa como el cerebro logístico de DianaBot, asegurando que:
- Los usuarios accedan al contenido correcto según su rol (gratuito o VIP).
- Las suscripciones y permisos se gestionen de forma automatizada y escalable.
- El contenido se publique de manera controlada, segura y personalizable.
- Los administradores tengan herramientas intuitivas para configurar canales, eventos y mensajes.
- Se integre con la narrativa y la gamificación para ofrecer una experiencia fluida.

Este sistema es esencial para mantener la sostenibilidad del bot, permitiendo monetización a través de suscripciones VIP y asegurando que el contenido sea accesible, seguro y relevante para los usuarios.

---

### **Funciones Principales**

#### **1. Gestión de Acceso a Canales**
El sistema controla quién puede interactuar con el bot y acceder a los canales gratuito y VIP, con mecanismos automatizados para validar y restringir accesos.

- **Canal Gratuito**:
  - **Acceso libre o condicional**: El administrador puede configurar si el canal gratuito es accesible para cualquier usuario que inicie el bot o si requiere unirse al canal primero.
  - **Validación periódica**: El bot verifica regularmente si los usuarios permanecen en el canal gratuito. Si un usuario lo abandona, puede ser expulsado del sistema o perder acceso a ciertas funciones.
  - **Incorporación automática**: Al iniciar el bot, los usuarios pueden ser aceptados automáticamente en el canal gratuito o pasar por un proceso de solicitud (por ejemplo, responder un mensaje o cumplir un requisito).
  - **Mensajes de bienvenida**: Envío automático de mensajes personalizados al unirse, con información sobre el canal, instrucciones o enlaces a la narrativa.

- **Canal VIP**:
  - **Validación de suscripción**: El bot comprueba si el usuario tiene una suscripción activa para acceder al canal VIP. Esto incluye verificar el tiempo restante de la suscripción.
  - **Expulsión automática**: Si la suscripción expira, el usuario es removido del canal VIP y pierde acceso a contenido exclusivo (niveles narrativos 4–6, misiones especiales, etc.).
  - **Gestión de reingresos**: Si un usuario renueva su suscripción, el bot restaura su acceso y sincroniza su progreso narrativo y de gamificación.
  - **Notificaciones de suscripción**:
    - Recordatorios automáticos antes de que expire la suscripción (por ejemplo, 3 días o 1 día antes).
    - Mensajes personalizados de renovación con enlaces o instrucciones para pagar.
    - Confirmaciones de cancelación o reincorporación.

#### **2. Gestión de Suscripciones**
El sistema administra las suscripciones VIP de manera integral, con herramientas para el administrador y automatizaciones para los usuarios.

- **Asignación de suscripciones**:
  - El administrador puede asignar manualmente acceso VIP a usuarios específicos (por ejemplo, como premio o promoción).
  - Configuración de la duración de la suscripción (días, semanas, meses).
  - Posibilidad de ofrecer suscripciones de prueba limitadas.

- **Seguimiento y control**:
  - Registro del estado de cada suscripción: activa, por expirar, expirada.
  - Panel administrativo para consultar suscripciones vigentes, fechas de vencimiento y usuarios activos.
  - Eliminación manual de usuarios VIP si es necesario (por ejemplo, por incumplimiento de reglas).

- **Automatizaciones**:
  - Expulsión automática de usuarios con suscripciones expiradas.
  - Envío de mensajes automáticos para:
    - Confirmar la activación de una suscripción.
    - Notificar vencimientos próximos.
    - Ofrecer opciones de renovación con enlaces o botones inline.
  - Posibilidad de personalizar el tono de los mensajes (por ejemplo, con la voz sarcástica de Lucien).

- **Flexibilidad**:
  - Configuración de precios o métodos de pago (externos, como links a plataformas de pago, ya que el bot no procesa pagos directamente).
  - Opciones para restringir contenido VIP a usuarios con ciertos logros o niveles de gamificación.

#### **3. Publicaciones y Gestión de Contenido**
El sistema permite al administrador programar, personalizar y proteger publicaciones, integrándolas con la narrativa y la gamificación.

- **Programación de publicaciones**:
  - **Calendario de publicaciones**: El administrador puede programar mensajes para fechas y horas específicas en ambos canales, con soporte para texto, imágenes, videos, stickers, encuestas o archivos.
  - **Publicaciones recurrentes**: Configuración de mensajes automáticos diarios, semanales o mensuales (por ejemplo, recordatorios de misiones, trivias o eventos narrativos).
  - **Edición y eliminación**: Gestión de un calendario de publicaciones futuras, con opciones para modificar o cancelar mensajes programados.

- **Botones inline interactivos**:
  - Los mensajes pueden incluir botones personalizados para:
    - Navegar entre menús (por ejemplo, acceder a la tienda, misiones o narrativa).
    - Registrar decisiones narrativas.
    - Confirmar acciones (como reclamar un regalo diario o participar en una trivia).
    - Redirigir a enlaces externos (por ejemplo, para renovar suscripciones).
  - Los botones son configurables por el administrador y pueden estar condicionados por el rol del usuario (gratuito o VIP).

- **Reacciones personalizadas**:
  - El bot permite predefinir reacciones (emojis o palabras clave) para publicaciones específicas.
  - Las reacciones pueden:
    - Desbloquear pistas narrativas.
    - Otorgar besitos (moneda virtual).
    - Registrar participación para misiones o logros.
  - Retroalimentación inmediata: El bot puede responder a las reacciones con mensajes personalizados (por ejemplo, “¡Bien hecho, Lucien aprueba tu elección!”).

- **Protección de contenido**:
  - **Mensajes protegidos**: El administrador puede marcar publicaciones como protegidas, desactivando la opción de reenvío o descarga (si Telegram lo permite).
  - **Restricción por rol**: Contenido exclusivo para usuarios VIP o con ciertos logros.
  - **Control de visibilidad**: Publicaciones visibles solo para usuarios que hayan completado fragmentos narrativos o misiones específicas.

#### **4. Gestión de Eventos Narrativos**
El sistema permite al administrador integrar eventos narrativos con los canales, conectándolos con la narrativa y la gamificación.

- **Eventos programados**:
  - Creación de eventos narrativos con fechas específicas (por ejemplo, lanzamiento de un nuevo nivel de la historia).
  - Publicaciones automáticas asociadas al evento, con botones inline para interactuar.
  - Restricción de eventos a usuarios VIP o con ciertos logros.

- **Mensajes narrativos**:
  - Envío de fragmentos narrativos como publicaciones en el canal, con decisiones interactivas (por ejemplo, botones para elegir entre dos caminos).
  - Posibilidad de ocultar fragmentos hasta que el usuario cumpla condiciones (como tener un objeto en la mochila o suficientes besitos).

- **Sincronización con narrativa**:
  - El sistema valida el progreso narrativo del usuario antes de mostrar contenido avanzado.
  - Publicaciones narrativas pueden incluir pistas ocultas que solo los usuarios con contexto narrativo entenderán.

#### **5. Panel Administrativo**
El módulo incluye un panel administrativo accesible mediante menús con teclados personalizados, diseñado para facilitar la gestión del bot.

- **Funciones del panel**:
  - **Configuración de canales**:
    - Definir si el canal gratuito es de acceso libre o restringido.
    - Configurar el canal VIP, incluyendo requisitos de suscripción y mensajes automáticos.
  - **Gestión de usuarios**:
    - Agregar o eliminar usuarios VIP manualmente.
    - Consultar estados de suscripción y progreso en narrativa/gamificación.
    - Expulsar usuarios por incumplimiento de reglas.
  - **Gestión de contenido**:
    - Programar, editar o eliminar publicaciones.
    - Configurar botones inline, reacciones o protección de mensajes.
  - **Configuración de gamificación**:
    - Activar/desactivar misiones, trivias o subastas.
    - Subir ítems a la tienda o configurar subastas.
  - **Estadísticas**:
    - Resumen de usuarios activos, suscripciones vigentes y participación en publicaciones.
    - Métricas de engagement (reacciones, participación en trivias, etc.).

- **Navegación intuitiva**:
  - Menús dinámicos con teclados personalizados para acceder a cada sección.
  - Comandos rápidos para tareas comunes (por ejemplo, expulsar un usuario o programar un mensaje).

#### **6. Notificaciones Automáticas**
El sistema envía notificaciones automáticas para mantener a los usuarios informados y enganchados.

- **Tipos de notificaciones**:
  - **Suscripciones**: Confirmaciones de activación, avisos de vencimiento, recordatorios de renovación.
  - **Eventos**: Anuncios de nuevos niveles narrativos, misiones o subastas.
  - **Reacciones**: Respuestas personalizadas a reacciones de usuarios (por ejemplo, “¡Lucien te guiña el ojo por tu reacción!”).
  - **Progreso**: Notificaciones sobre logros, misiones completadas o ítems obtenidos.

- **Personalización**:
  - Los mensajes pueden adoptar el tono sarcástico y elegante de Lucien.
  - Posibilidad de incluir chistes o frases personalizadas para reforzar la temática del bot.

#### **7. Seguridad y Control**
El módulo prioriza la seguridad del contenido y los datos de los usuarios.

- **Protección contra reenvíos**: Mensajes marcados como protegidos no pueden ser reenviados ni descargados.
- **Validación de accesos**: Verificación constante de membresías para evitar accesos no autorizados.
- **Restricción por rol**: Contenido exclusivo para usuarios VIP o con logros específicos.
- **Gestión de expulsiones**: Expulsión automática de usuarios con suscripciones expiradas o que abandonen el canal gratuito.

---

### **Conexiones con Otros Módulos**

#### **Con Narrativa Inmersiva**
- **Acceso a niveles narrativos**:
  - Los niveles 1–3 de la narrativa están disponibles en el canal gratuito, mientras que los niveles 4–6 requieren suscripción VIP.
  - El sistema valida el rol del usuario antes de mostrar contenido narrativo avanzado.
- **Publicaciones narrativas**:
  - Los fragmentos narrativos se publican como mensajes en los canales, con botones inline para tomar decisiones.
  - Algunos fragmentos están protegidos o restringidos a usuarios con ciertos logros o ítems.
- **Eventos narrativos**:
  - El administrador puede programar eventos narrativos (por ejemplo, un nuevo capítulo) que se integren con el calendario de publicaciones.
  - Las pistas narrativas pueden ocultarse en publicaciones “inocentes” que requieren atención del usuario.

#### **Con Gamificación**
- **Reacciones y puntos**:
  - Las reacciones a publicaciones otorgan besitos, registradas automáticamente por el sistema.
  - Publicaciones pueden incluir trivias o misiones que generan recompensas.
- **Restricción de contenido gamificado**:
  - Subastas, trivias o misiones exclusivas están limitadas a usuarios VIP.
  - El sistema valida el rol del usuario antes de permitir participación.
- **Publicaciones interactivas**:
  - Mensajes con botones inline pueden iniciar misiones, abrir la tienda o registrar pujas en subastas.
  - Las publicaciones pueden recompensar con besitos o ítems al interactuar.

---

### **Acciones Específicas del Bot**

1. **Validación automática**:
   - Comprobar membresía en canales gratuito y VIP.
   - Expulsar usuarios con suscripciones expiradas o que abandonen el canal gratuito.

2. **Envío de mensajes**:
   - Publicaciones programadas o en tiempo real con multimedia, botones inline y reacciones personalizadas.
   - Mensajes protegidos contra reenvío o descarga.

3. **Gestión de suscripciones**:
   - Asignar, modificar o eliminar suscripciones VIP.
   - Enviar recordatorios y confirmaciones automáticas.

4. **Programación de eventos**:
   - Crear eventos narrativos o gamificados con fechas específicas.
   - Publicar mensajes con decisiones narrativas o desafíos.

5. **Interacciones dinámicas**:
   - Registrar reacciones para otorgar besitos o desbloquear contenido.
   - Gestionar botones inline para navegar o tomar decisiones.

6. **Panel administrativo**:
   - Configurar canales, publicaciones, suscripciones y contenido gamificado.
   - Consultar estadísticas de usuarios y engagement.

---

### **Impacto y Relevancia**
El módulo de administración de canales es el componente que hace sostenible y escalable a DianaBot:
- **Monetización**: Facilita la gestión de suscripciones VIP, una fuente clave de ingresos.
- **Control**: Asegura que el contenido llegue solo a los usuarios autorizados, protegiendo la propiedad intelectual y la experiencia exclusiva.
- **Personalización**: Permite al administrador adaptar publicaciones, eventos y mensajes al tono y objetivos del bot.
- **Integración**: Conecta narrativa y gamificación mediante publicaciones interactivas, reacciones y eventos, creando una experiencia unificada.
- **Escalabilidad**: Soporta canales de cualquier tamaño, con herramientas para gestionar miles de usuarios y publicaciones.

---

### **Resumen Técnico**
El sistema de administración de canales es un módulo robusto que combina:
- **Gestión de accesos**: Validación automática de membresías y expulsión de usuarios no autorizados.
- **Control de suscripciones**: Seguimiento, notificaciones y personalización de suscripciones VIP.
- **Publicaciones avanzadas**: Programación, protección y personalización de contenido con botones inline y reacciones.
- **Panel administrativo**: Menús intuitivos para configurar canales, usuarios, contenido y estadísticas.
- **Seguridad**: Protección de mensajes y validación constante de permisos.

**Ejemplo de flujo**:
1. Un usuario se une al canal gratuito y recibe un mensaje de bienvenida con un botón para iniciar la narrativa.
2. Al intentar acceder al canal VIP, el bot valida su suscripción; si no está activa, envía un enlace de renovación.
3. El administrador programa una publicación con un fragmento narrativo exclusivo para VIP, protegido contra reenvío, que incluye un botón para elegir un camino en la historia.
4. Las reacciones a la publicación otorgan besitos, y el sistema registra la participación para desbloquear una misión.

---

### **Conclusión**
El módulo de administración de canales es el núcleo operativo de DianaBot, proporcionando las herramientas necesarias para gestionar usuarios, suscripciones y contenido de manera eficiente y segura. Su integración con la narrativa y la gamificación asegura que las acciones de los usuarios tengan un impacto directo en su experiencia, mientras que las funciones administrativas permiten al equipo personalizar y escalar el bot según sus necesidades. Este sistema no solo garantiza la sostenibilidad del proyecto, sino que también refuerza la inmersión y el engagement al conectar todos los elementos del ecosistema en una experiencia fluida y contrastada/
