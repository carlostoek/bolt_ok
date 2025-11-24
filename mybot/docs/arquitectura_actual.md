# Análisis de Arquitectura del Bot de Telegram

Este documento detalla la arquitectura, módulos y flujos de datos del bot de Telegram, basado en el análisis del código fuente.

## 1. Arquitectura General

### Stack Tecnológico
- **Lenguaje:** Python
- **Framework del Bot:** [Aiogram](https://aiogram.dev/), un framework asíncrono moderno para la API de Telegram.
- **Base de Datos:** [SQLAlchemy](https://www.sqlalchemy.org/) (con su extensión `asyncio`) como ORM. Esto permite que el bot sea agnóstico a la base de datos subyacente, aunque la documentación y configuración sugieren compatibilidad con **PostgreSQL** y **SQLite**.
- **Migraciones de BD:** [Alembic](https://alembic.sqlalchemy.org/en/latest/), integrado con SQLAlchemy para gestionar la evolución del esquema de la base de datos.

### Estructura de Directorios y Organización del Código
El proyecto sigue una estructura organizada y modular:
- `handlers/`: Contiene la lógica para responder a los comandos del bot, callbacks de botones y otros eventos de Telegram. Se subdivide por funcionalidad (admin, user, narrative, shop, etc.).
- `database/`: Define los modelos de datos con SQLAlchemy (`models.py`, `narrative_models.py`), la configuración de la conexión (`setup.py`) y las migraciones de Alembic.
- `services/`: Encapsula la lógica de negocio principal (ej: `narrative_service.py`, `shop_service.py`). Los handlers delegan en estos servicios para realizar las operaciones complejas.
- `core/`: Define las interfaces y componentes fundamentales, como los repositorios base.
- `config/`: Almacena archivos de configuración estáticos, como los schemas JSON para la narrativa (`narrative_schema.json`).
- `keyboards/`: Lógica para crear los teclados interactivos (botones inline y de respuesta) que se muestran a los usuarios.
- `docs/`: Documentación extensa sobre la arquitectura, flujos y decisiones de diseño.
- `tests/`: Pruebas automatizadas para garantizar la calidad del código.

### Dependencias Principales
Aunque `requirements.txt` está malformado, el análisis del código revela las siguientes dependencias clave:
- `aiogram`: Framework principal del bot.
- `sqlalchemy`: ORM para toda la interacción con la base de datos.
- `alembic`: Herramienta para migraciones de base de datos.

## 2. Módulo de Narrativa

El módulo de narrativa es el corazón de la experiencia y está diseñado de forma flexible usando un sistema de grafos.

### Modelo de Datos de Fragmentos
El modelo principal es `StoryFragment`, que representa un nodo en la historia.

```python
# database/narrative_models.py

class StoryFragment(Base):
    __tablename__ = 'story_fragments'

    id = Column(Integer, primary_key=True)
    key = Column(String(50), unique=True, nullable=False) # Identificador de negocio
    text = Column(Text, nullable=False)
    image_url = Column(String(500), nullable=True)
    
    # Requisitos para acceder
    min_besitos = Column(Integer, default=0)
    required_role = Column(String, nullable=True, index=True)
    
    # Recompensa por llegar
    reward_besitos = Column(Integer, default=0)
    
    # Siguiente fragmento (si no hay decisión)
    auto_next_fragment_key = Column(String(50), nullable=True)

    # Relación con las decisiones que parten de este fragmento
    choices = relationship(
        "NarrativeChoice", 
        back_populates="source_fragment", 
        foreign_keys="NarrativeChoice.source_fragment_id",
        cascade="all, delete-orphan"
    )
```

### Cómo se Almacenan las Decisiones y sus Consecuencias
Las decisiones son arcos que conectan los nodos (`StoryFragment`). Se modelan con `NarrativeChoice`.

```python
# database/narrative_models.py

class NarrativeChoice(Base):
    __tablename__ = 'narrative_choices'

    id = Column(Integer, primary_key=True)
    source_fragment_id = Column(Integer, ForeignKey('story_fragments.id'), nullable=False)
    destination_fragment_key = Column(String(50), nullable=False) # A dónde lleva la decisión
    text = Column(String, nullable=False) # Texto del botón
    
    # Requisitos para que la opción sea visible/usable
    required_besitos = Column(Integer, default=0)
    required_role = Column(String, nullable=True)
```

El progreso del usuario se guarda en `UserNarrativeState`, que registra el fragmento actual y las decisiones tomadas.

```python
# database/narrative_models.py

class UserNarrativeState(Base):
    __tablename__ = 'user_narrative_states'

    user_id = Column(BigInteger, ForeignKey('users.id'), primary_key=True)
    current_fragment_key = Column(String(50), nullable=True)
    choices_made = Column(JSON, default=list) # Historial de decisiones
    unlocked_fragments = Column(JSON, default=list) # Fragmentos desbloqueados (ej. por compra)
```

### Sistema de Bloqueo/Desbloqueo de Contenido
El acceso a fragmentos y decisiones se puede restringir mediante:
1.  **Puntos:** `StoryFragment.min_besitos` y `NarrativeChoice.required_besitos`.
2.  **Roles:** `StoryFragment.required_role` y `NarrativeChoice.required_role` (ej: "vip").
3.  **Desbloqueo explícito:** La lista `UserNarrativeState.unlocked_fragments` permite dar acceso a fragmentos específicos, por ejemplo, tras una compra en la tienda.

### Relaciones entre Fragmentos (Árbol de Decisiones)
El árbol se construye mediante la relación entre `StoryFragment` y `NarrativeChoice`. Cada `NarrativeChoice` actúa como un arco dirigido que conecta un `source_fragment_id` con un `destination_fragment_key`. Esto permite crear narrativas ramificadas complejas. Los fragmentos lineales usan `auto_next_fragment_key` para avanzar automáticamente.

### Identificadores Únicos Usados
- **`StoryFragment.key`**: Es el identificador de negocio principal. Es una cadena de texto legible (ej: `CAP1_ESCENA_01`) que desacopla la lógica del `id` numérico autoincremental. Esto facilita la creación y migración de contenido narrativo desde archivos JSON.
- **`NarrativeChoice.id`**: Clave primaria para las decisiones.
- **`User.id`**: ID de usuario de Telegram, que vincula al jugador con su estado narrativo.

## 3. Módulo de Gamificación

El bot incluye un sistema de gamificación robusto para incentivar la participación.

### Sistema de Puntos
- Los puntos (llamados "besitos" o `points`) se almacenan en el modelo `User`: `points = Column(Float, default=0)`.
- **Cómo se otorgan:**
    - Al llegar a un `StoryFragment` (`reward_besitos`).
    - Al completar una `Mission` (`reward_points`).
    - Al reaccionar a publicaciones en canales (`Channel.reaction_points`).
    - Al completar un `Trivia` (`reward_points`).
- **Cómo se consumen:**
    - Al elegir una `NarrativeChoice` con coste (`required_besitos`).
    - Al comprar un `ShopItem` (`price`).
    - Al jugar un minijuego (`MiniGamePlay.cost_points`).

### Estructura de Recompensas y Misiones
- **Misiones (`Mission`):** Tareas que los usuarios pueden completar para ganar puntos. Tienen un tipo (`one_time`, `daily`), un objetivo (`target_value`) y una recompensa. El progreso se guarda en `UserMissionEntry`. Las misiones pueden estar encadenadas.
- **Recompensas (`Reward`):** Premios que se desbloquean al alcanzar un umbral de puntos (`required_points`).
- **Logros y Medallas (`Achievement`, `Badge`):** Reconocimientos adicionales por cumplir ciertas condiciones.

### Sistema de Widgets
El término "widget" no se usa explícitamente, pero se refiere a los módulos interactivos de gamificación:
- **Sorteos (`Raffle`):** Sistema para crear sorteos en los que los usuarios pueden participar.
- **Subastas (`Auction`):** Un sistema de pujas en tiempo real donde los usuarios usan sus puntos.
- **Trivias (`Trivia`):** Cuestionarios con preguntas y respuestas que otorgan puntos.
- **Desafíos (`Challenge`):** Competiciones de tiempo limitado (diarias, semanales) basadas en acciones específicas.

### Integración con Narrativa
La gamificación y la narrativa están profundamente entrelazadas:
- Completar una `Mission` puede desbloquear una `LorePiece` (pieza de historia).
- Comprar un `ShopItem` puede desbloquear un `StoryFragment` (`unlocks_fragment_key`) o una `LorePiece`.
- Alcanzar un `StoryFragment` puede desbloquear un `Achievement`.

## 4. Módulo de Administración de Canales

### Estados de Usuario
El modelo `User` gestiona los diferentes estados y roles:
- `role = Column(String, default="free")`: El rol principal del usuario (ej: "free", "vip").
- `vip_expires_at = Column(DateTime, nullable=True)`: Controla la membresía VIP temporal.
- `is_admin = Column(Boolean, default=False)`: Define a los administradores del bot.

### Sistema de Reacciones y Eventos
- **Reacciones Nativas:** El modelo `Channel` permite configurar qué emojis de reacción están permitidos y cuántos puntos otorgan (`reaction_points`).
- **Reacciones por Botones:** El modelo `ButtonReaction` registra clics en teclados personalizados adjuntos a mensajes de un canal.
- **Eventos Especiales:** El modelo `Event` permite crear eventos de tiempo limitado, como multiplicadores de puntos (ej: "Doble de puntos este fin de semana").

### Permisos y Roles
El acceso a contenido y funcionalidades se controla principalmente a través del `User.role`:
- **Narrativa:** `StoryFragment.required_role` y `NarrativeChoice.required_role`.
- **Tienda:** `ShopItem.is_vip_only`.
- **Comandos de Admin:** La lógica en los `handlers/admin/` comprueba el flag `User.is_admin`.

## 5. Tienda

### Modelo de Productos
El producto está modelado por `ShopItem`, que contiene su nombre, descripción, precio, imagen y reglas de negocio. Un `ShopItem` puede estar asociado a múltiples archivos (`ProductFile`), útil para vender sets de fotos o contenido multimedia.

```python
# database/models.py

class ShopItem(Base):
    __tablename__ = "shop_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(Integer, nullable=False) # Precio en puntos
    is_vip_only = Column(Boolean, default=False)
    
    # ¿Qué desbloquea este item?
    unlocks_lore_piece_id = Column(Integer, ForeignKey("lore_pieces.id"), nullable=True)
    unlocks_fragment_key = Column(String(50), nullable=True)
    
    # Reglas de disponibilidad y stock
    stock_limit = Column(Integer, nullable=True)
    max_purchases_per_user = Column(Integer, default=1)
    available_from = Column(DateTime, nullable=True)
    available_until = Column(DateTime, nullable=True)
    
    # Requisitos de compra complejos
    unlock_requirements = Column(JSON, nullable=True)
```

### Tipos de Productos
El tipo de producto se define por lo que desbloquea:
- **Desbloqueo de Narrativa:** Items que rellenan `unlocks_fragment_key`.
- **Desbloqueo de Lore:** Items que rellenan `unlocks_lore_piece_id`.
- **Acceso VIP:** No hay un campo directo, pero la lógica de compra puede otorgar un `VipGrant` o un `Reward` que a su vez da días de VIP.
- **Contenido Multimedia:** Items que entregan `ProductFile`.

### Sistema de Compra y Validación
El proceso, gestionado en `handlers/shop_handlers.py`, implica:
1.  Verificar que el usuario tiene puntos suficientes.
2.  Comprobar el stock (`stock_limit`) y el límite de compra por usuario (`max_purchases_per_user`).
3.  Validar la disponibilidad por fecha y rol (`available_from`, `is_vip_only`).
4.  Si todo es correcto, se restan los puntos al usuario, se crea un registro en `UserPurchase` y se entrega el producto (desbloqueando el contenido o enviando los archivos).

### Referencias Cruzadas
- `ShopItem.unlocks_fragment_key` -> `StoryFragment.key`
- `ShopItem.unlocks_lore_piece_id` -> `LorePiece.id`
- `UserPurchase` -> `User.id` y `ShopItem.id`

## 6. Configuración Actual

### Archivos de Configuración Existentes
- `alembic.ini`: Configuración para las migraciones de base de datos.
- `config/narrative_schema.json`: Define la estructura esperada para los archivos JSON de narrativa.
- `config/decision_requirements.json`: Parece ser un archivo de configuración para la lógica de decisiones.
- `data/*.json`: Contienen datos iniciales para trivias, quizzes, etc.

### Formato de Datos
- **Base de Datos:** La fuente principal de verdad para todos los datos dinámicos (usuarios, progreso, etc.).
- **JSON:** Utilizado para la carga inicial de contenido estático como la narrativa y las trivias. Esto permite a los diseñadores narrativos trabajar en archivos de texto sencillos que luego se cargan en la base de datos.

### Proceso Actual de Creación/Vinculación de Elementos
1.  **Narrativa:** Se crea un archivo JSON siguiendo el schema. Un script (`populate_narrative.py` o similar) lee este JSON y lo inserta en las tablas `story_fragments` y `narrative_choices`, resolviendo las referencias por `key`.
2.  **Tienda, Misiones, etc.:** Se crean a través de paneles de administración dentro del propio bot (gestionados en `handlers/admin/`). Estos paneles interactúan directamente con la base de datos a través de los servicios.

### Pain Points Identificados en el Flujo de Configuración
- **Dependencia de JSONs:** Mantener la consistencia entre múltiples archivos JSON de narrativa puede ser complejo. Un error de sintaxis o una `key` mal escrita puede romper el flujo.
- **Vinculación Manual:** La vinculación entre módulos (ej: un `ShopItem` que desbloquea un `StoryFragment`) depende de que el administrador introduzca la `key` correcta manualmente en el panel de admin. Esto es propenso a errores.
- **Falta de un CMS Unificado:** La configuración está dividida entre archivos JSON y paneles de admin dentro del bot. Un CMS web externo podría centralizar y simplificar la gestión de todo el contenido (narrativa, tienda, misiones) con validación y selectores visuales para evitar errores de tipeo.

## 7. APIs y Endpoints

### Comandos del Bot Expuestos
Los handlers en `handlers/` definen los comandos. Los principales son:
- `/start`: Inicia la interacción con el bot.
- `/menu`: Muestra el menú principal.
- Comandos de admin (ej: `/admin`, `/shop_admin`): Acceden a los paneles de gestión.
- El bot responde a callbacks de botones en lugar de a muchos comandos de texto.

### APIs Externas
No se evidencia una API REST/GraphQL pública expuesta por el bot. La comunicación es interna o a través de la API de Telegram.

### Webhooks de Telegram
El bot funciona en modo webhook (preferido para producción). El punto de entrada principal (`bot.py` o similar) configura el dispatcher de Aiogram para recibir las actualizaciones de Telegram.

## 8. Interconexiones Críticas

### Mapa de Dependencias entre Módulos
- **Usuario (`User`)** es el modelo central. Todo se vincula a él.
- **Narrativa (`StoryFragment`)** se conecta con **Gamificación** (`Achievement`, `Mission`) y **Tienda** (`ShopItem`).
- **Tienda (`ShopItem`)** es un nexo clave, pudiendo desbloquear contenido en casi todos los demás módulos (Narrativa, Lore, VIP).
- **Gamificación (`Mission`, `Level`)** desbloquea `LorePiece`, que es una forma de narrativa ligera.

### Flujos de Datos
- **Usuario completa un fragmento narrativo:**
    1.  El `narrative_handler` recibe el callback de la decisión del usuario.
    2.  Llama al `narrative_service` para validar la elección.
    3.  El servicio actualiza el `UserNarrativeState` (cambia `current_fragment_key`, añade la decisión a `choices_made`).
    4.  Otorga puntos (`User.points += reward_besitos`).
    5.  Comprueba si se desbloquea un `Achievement`.
    6.  Envía el nuevo `StoryFragment` al usuario.

- **Usuario reacciona a una publicación:**
    1.  El `reaction_handler` recibe el evento `MessageReactionUpdated`.
    2.  Busca en el modelo `Channel` los puntos asociados a esa reacción.
    3.  Llama al `point_service` para añadir los puntos al `User`.
    4.  El `point_service` puede a su vez llamar al `level_service` o `achievement_service` para ver si la ganancia de puntos desbloquea algo.

- **Usuario compra un producto:**
    1.  El `shop_handler` recibe el callback de compra.
    2.  Llama al `shop_service` para validar la compra (puntos, stock, etc.).
    3.  Si es válida, el servicio resta los puntos al `User` y crea un `UserPurchase`.
    4.  El servicio determina qué desbloquea el item (`unlocks_fragment_key`, `unlocks_lore_piece_id`, etc.).
    5.  Llama al servicio correspondiente (ej: `narrative_service`) para otorgar el acceso.
    6.  Notifica al usuario de la compra exitosa.

- **Usuario completa una misión:**
    1.  Un `middleware` o un `handler` específico detecta la acción que cumple la misión (ej: enviar X mensajes).
    2.  Actualiza el `UserMissionEntry` marcando la misión como completada.
    3.  Llama al `point_service` para otorgar los `reward_points`.
    4.  Comprueba si la misión desbloquea una `LorePiece` o una misión subsecuente.
    5.  Notifica al usuario a través de un `notifier_service`.


### **Documento Técnico: Análisis Interno del Bot para Panel de Administración Unificado**

**Versión:** 1.0
**Fecha:** 2024-10-26
**Objetivo:** Describir la arquitectura, entidades y procesos actuales del bot para guiar el desarrollo de un panel de administración web que centralice y automatice la configuración.

---

### **1. ENTIDADES DEL SISTEMA**

A continuación se describen las entidades principales identificadas en el código, principalmente a través de los modelos de la base de datos (`database/models.py`, `database/narrative_models.py`, etc.).

#### **1.1. User (Perfil de Usuario)**
*   **Descripción funcional:** Representa a un usuario final del bot. Almacena su información de Telegram, estado en el sistema (VIP, baneado), inventario y progreso.
*   **Atributos actuales:** `id`, `user_id` (Telegram), `username`, `first_name`, `last_name`, `is_vip`, `vip_expiration`, `is_banned`, `created_at`, `updated_at`, `pending_decision`.
*   **Relación con otras entidades:**
    *   Tiene un **Inventario** (uno a muchos con `InventoryItem`).
    *   Tiene un registro de **Fragmentos Vistos** (uno a muchos con `UserFragmentView`).
    *   Puede tener **Regalos Recibidos** (uno a muchos con `UserGift`).
*   **Dependencias:** Ninguna. Es una entidad raíz creada cuando un nuevo usuario interactúa con el bot.
*   **Efectos:** Su estado (`is_vip`, `is_banned`) condiciona el acceso a ciertos comandos y flujos del bot.

#### **1.2. NarrativeFragment (Fragmento de Narrativa)**
*   **Descripción funcional:** Es la unidad atómica de la narrativa. Contiene un segmento de la historia, que puede ser texto, una imagen o un video. Puede estar bloqueado o ser de acceso libre.
*   **Atributos actuales:** `id`, `fragment_id` (string, ID legible), `content` (texto del fragmento), `media_type` (e.g., 'photo', 'video'), `media_id` (ID de archivo de Telegram), `is_locked`, `unlock_product_id`, `parent_id`.
*   **Relación con otras entidades:**
    *   Puede ser desbloqueado por un **Product** (relación `unlock_product_id` -> `Product.id`).
    *   Puede tener un **Lore** asociado (relación a través de tablas de unión o lógica de servicio).
    *   Forma una secuencia a través de `parent_id`.
*   **Dependencias:** Para un fragmento bloqueado, necesita que exista un **Product** cuyo ID se asignará a `unlock_product_id`.
*   **Efectos:** Cuando un usuario accede a un fragmento, se crea un registro `UserFragmentView`. Si está bloqueado, el sistema impide el acceso hasta que se cumpla la condición de desbloqueo (generalmente, tener el producto asociado en el inventario).

#### **1.3. Lore**
*   **Descripción funcional:** Representa una pieza de conocimiento o trasfondo del mundo narrativo. Se desbloquea y se muestra al usuario.
*   **Atributos actuales:** `id`, `lore_id` (string), `title`, `content`, `is_unlocked_by_default`.
*   **Relación con otras entidades:** Su desbloqueo suele estar ligado a la visualización de ciertos **NarrativeFragment** o a la realización de acciones específicas, gestionado a través de la lógica de los `handlers`.
*   **Dependencias:** Existe de forma independiente, pero su utilidad depende de estar asociado a un trigger o evento en la narrativa.
*   **Efectos:** Cuando se desbloquea, se vuelve visible para el usuario en la sección de "Lore" del bot.

#### **1.4. Product (Producto de la Tienda)**
*   **Descripción funcional:** Un artículo que se puede comprar en la tienda del bot. Su propósito principal es actuar como "llave" para desbloquear contenido narrativo.
*   **Atributos actuales:** `id`, `name`, `description`, `price`, `stock`, `image_url`, `is_active`.
*   **Relación con otras entidades:**
    *   Puede desbloquear un **NarrativeFragment** (un producto desbloquea un fragmento).
    *   Los usuarios pueden poseerlo a través del **Inventory**.
*   **Dependencias:** Ninguna. Es una entidad independiente.
*   **Efectos:** Cuando un usuario lo compra, se añade a su inventario y se descuenta el coste. Si el producto está asociado a un fragmento bloqueado, el usuario gana acceso a dicho fragmento.

#### **1.5. InventoryItem (Elemento de Inventario)**
*   **Descripción funcional:** Representa la posesión de un producto por parte de un usuario.
*   **Atributos actuales:** `id`, `user_id`, `product_id`, `quantity`, `acquired_at`.
*   **Relación con otras entidades:** Es una tabla de unión entre **User** y **Product**.
*   **Dependencias:** Necesita que existan un `User` y un `Product`.
*   **Efectos:** La existencia de un `InventoryItem` en el inventario de un usuario es la condición que el sistema verifica para conceder acceso a contenido bloqueado.

#### **1.6. Trigger/Condition (Disparador/Condición)**
*   **Descripción funcional:** No es una entidad de base de datos única, sino un concepto implementado en la lógica de los `handlers` y en archivos de configuración como `config/decision_requirements.json`. Define una causa (e.g., "usuario ve el fragmento X") y un efecto (e.g., "desbloquear recompensa Y").
*   **Atributos actuales (Conceptuales):** `trigger_type` (e.g., 'VIEW_FRAGMENT', 'PURCHASE_PRODUCT'), `trigger_source_id`, `reward_type`, `reward_id`.
*   **Relación con otras entidades:** Conecta **Acciones del Usuario** con **Recompensas**.
*   **Dependencias:** Depende de la existencia de las entidades que actúan como causa (e.g., `NarrativeFragment`) y efecto (`Reward`).
*   **Efectos:** Automatiza la entrega de recompensas o el cambio de estado basado en las acciones del usuario.

#### **1.7. Reward (Recompensa)**
*   **Descripción funcional:** Al igual que los Triggers, no parece ser una tabla única, sino una lógica distribuida. Representa algo que el usuario recibe automáticamente. Puede ser un producto, acceso VIP temporal o un mensaje especial.
*   **Atributos actuales (Conceptuales):** `reward_type` (e.g., 'GIVE_PRODUCT', 'GRANT_VIP'), `product_id` (si es un producto), `duration_days` (si es VIP).
*   **Relación con otras entidades:** Se activa por un **Trigger**. Afecta al **User** (otorgando VIP) o a su **Inventory** (añadiendo un producto).
*   **Dependencias:** Depende de la existencia de un `Product` si la recompensa es un producto.
*   **Efectos:** Modifica el perfil o inventario del usuario.

#### **1.8. Automated Journey**
*   **Descripción funcional:** Es un proceso, no una entidad. Se define en los `handlers` (e.g., `daily_gift.py`) y servicios. Consiste en una secuencia de interacciones o entregas de contenido programadas en el tiempo (e.g., un mensaje diario durante 7 días).
*   **Atributos (Conceptuales):** `journey_name`, `sequence_of_steps` (lista de mensajes/acciones), `time_delay_between_steps`.
*   **Relación con otras entidades:** Interactúa con **User** para rastrear el progreso del journey de cada uno. Puede entregar **NarrativeFragment** o **Rewards**.
*   **Dependencias:** Requiere que el contenido (fragmentos, mensajes) a entregar ya exista.
*   **Efectos:** Envía mensajes proactivos a los usuarios que están en un journey específico.

---

### **2. PROCESOS DEL SISTEMA**

Análisis de los flujos de configuración actuales, basados en los `handlers` de administración.

#### **2.1. Crear y Configurar un Nuevo Fragmento Bloqueado**
*   **Objetivo:** Añadir un nuevo capítulo a la historia que solo sea accesible tras comprar un artículo en la tienda.
*   **Flujo actual paso a paso:**
    1.  **Paso Manual (Fuera del bot):** El administrador prepara el contenido (texto, ID de la imagen/video ya subida a Telegram).
    2.  **Paso Manual (Proceso 1 - Crear Producto):** El administrador usa el comando `/admin_tienda` -> "Crear Producto".
    3.  El bot pide nombre, descripción, precio, etc. El administrador los introduce.
    4.  El producto se crea en la base de datos. El bot **no devuelve el ID del producto creado**.
    5.  **Paso Manual:** El administrador debe consultar la base de datos directamente o usar otro comando (si existe) para obtener el `product_id` del producto recién creado.
    6.  **Paso Manual (Proceso 2 - Crear Fragmento):** El administrador usa `/admin_narrativa` -> "Crear Fragmento".
    7.  El bot pide un `fragment_id` (texto legible, e.g., "capitulo_5_intro").
    8.  El bot pide el contenido (texto) y opcionalmente el `media_id` de Telegram.
    9.  El bot pregunta si el fragmento está bloqueado (`is_locked`). El administrador responde "Sí".
    10. **Paso Manual (Copia de ID):** El bot pide el `unlock_product_id`. El administrador debe pegar el ID obtenido en el paso 5.
    11. El fragmento se crea en la base de datos, con la relación al producto establecida.
*   **Entidades que intervienen:** `Product`, `NarrativeFragment`.
*   **Pasos/Relaciones manuales:**
    *   Creación de producto y fragmento como dos procesos separados.
    *   Obtención manual del `product_id`.
    *   Copia y pega manual del `product_id` en el flujo de creación del fragmento.
*   **Errores comunes:** Pegar un `product_id` incorrecto o inexistente, lo que rompe el flujo de desbloqueo para el usuario. Olvidar crear el producto primero.
*   **Limitaciones:** Proceso fragmentado y muy propenso a errores humanos. No hay validación de que el `product_id` introducido sea correcto en el momento de la creación.

#### **2.2. Configurar Recompensas y Triggers**
*   **Objetivo:** Otorgar automáticamente un objeto o beneficio cuando un usuario realiza una acción específica.
*   **Flujo actual paso a paso:**
    1.  Este proceso no parece tener un panel de administración dentro del bot. La lógica está "hardcodeada" en los `handlers`.
    2.  **Paso Manual (Código):** Un desarrollador debe editar el fichero del `handler` correspondiente a la acción que servirá de trigger (e.g., `narrative_handler.py`).
    3.  Dentro de la función que maneja la acción (e.g., `display_fragment`), el desarrollador añade una comprobación: `if fragment.id == 'ID_DEL_TRIGGER':`.
    4.  **Paso Manual (Código):** A continuación, añade la lógica para otorgar la recompensa: llamar a un servicio que añada un producto al inventario (`add_item_to_inventory(user_id, reward_product_id)`) o que modifique el estado del usuario.
    5.  **Paso Manual (IDs):** Los IDs del fragmento trigger y del producto recompensa deben ser escritos directamente en el código.
*   **Entidades que intervienen:** `User`, `InventoryItem`, `Product`, `NarrativeFragment`.
*   **Pasos/Relaciones manuales:** Todo el proceso es manual y requiere modificar y redesplegar el código del bot.
*   **Errores comunes:** Errores de tipeo en los IDs, lógica incorrecta que crea bucles o entrega recompensas múltiples veces.
*   **Limitaciones:** Cero flexibilidad. No es administrable por alguien sin acceso al código. Extremadamente rígido y no escalable.

---

### **3. MENÚ ACTUAL DEL BOT (ADMINISTRACIÓN)**

Basado en el análisis de los `command handlers` y `conversation handlers` en `handlers/admin.py`, `handlers/admin_narrative_handlers.py`, etc.

*   **/admin** (Menú Principal de Administración)
    *   **Gestión de Usuarios:**
        *   *Ver/Buscar Usuario:* Pide un `user_id` de Telegram y muestra sus datos.
        *   *Conceder VIP:* Pide `user_id` y duración. Afecta a `User.is_vip`.
        *   *Revocar VIP:* Pide `user_id`. Afecta a `User.is_vip`.
        *   *Banear Usuario:* Pide `user_id`. Afecta a `User.is_banned`.
    *   **Gestión de Narrativa (redirige a `/admin_narrativa`):**
        *   *Crear Fragmento:* Inicia el proceso descrito en 2.1.
        *   *Editar Fragmento:* Pide `fragment_id`, luego permite modificar campos.
        *   *Listar Fragmentos:* Muestra una lista de todos los fragmentos.
        *   *Crear Lore:* Similar a crear un fragmento, pero para la entidad `Lore`.
    *   **Gestión de Tienda (redirige a `/admin_tienda`):**
        *   *Crear Producto:* Inicia el proceso de creación de `Product`.
        *   *Editar Producto:* Permite cambiar precio, stock, etc.
        *   *Activar/Desactivar Producto:* Cambia `Product.is_active`.
    *   **Anuncios Globales:**
        *   *Enviar Mensaje a Todos:* Envía un mensaje masivo a todos los usuarios.
        *   *Enviar Mensaje a VIPs:* Envía un mensaje solo a usuarios VIP.

*   **Análisis del Menú:**
    *   **Dependencias:** El menú de Narrativa y el de Tienda están separados, pero sus entidades están fuertemente acopladas (un fragmento bloqueado necesita un producto). El flujo de trabajo obliga al administrador a saltar entre menús.
    *   **Elementos Duplicados:** No se observan opciones duplicadas, pero sí flujos de trabajo redundantes y fragmentados.
    *   **Elementos Aislados:** La configuración de Triggers y Recompensas está completamente aislada del panel, viviendo solo en el código. La gestión de Journeys y Regalos Automáticos también parece estar en `scripts` o `handlers` separados sin una interfaz de administración.

---

### **4. MAPA DE DEPENDENCIAS ENTRE MÓDULOS**

*   **Jerarquía de Entidades:**
    1.  **Nivel 0 (Independientes):** `User`, `Product`, `Lore`. Pueden existir por sí solos.
    2.  **Nivel 1 (Dependen de Nivel 0):** `InventoryItem` (depende de `User` y `Product`), `NarrativeFragment` (un fragmento bloqueado depende de `Product`).
    3.  **Nivel 2 (Lógica sobre entidades):** `Trigger`, `Reward`, `Journey`. No son tablas, sino lógica que opera sobre las entidades existentes. Un `Trigger` de "ver fragmento" depende de `NarrativeFragment`. Una `Reward` de "dar producto" depende de `Product`.

*   **Flujos de Procesos:**
    *   `Crear Contenido Bloqueado` **requiere** `Crear Producto` primero.
    *   `Configurar Recompensa` **requiere** que el `Producto` a regalar o el `Fragmento` que actúa como trigger ya existan.
    *   El `Sistema de Inventario` es el **origen** de la verificación para el `Acceso a Contenido`.
    *   Una `Acción de Usuario` (e.g., ver un fragmento) es el **origen** de un `Trigger`, que a su vez es el **origen** de una `Recompensa`.

*   **Árbol de Dependencias (Simplificado):**
    ```
    (Código) Trigger/Reward Logic
        └── (Requiere) NarrativeFragment (como causa)
        └── (Requiere) Product (como recompensa)

    (Admin) Crear NarrativeFragment (Bloqueado)
        └── (Requiere ID de) Product

    (Usuario) Acceso a Fragmento Bloqueado
        └── (Verifica) InventoryItem
            ├── (Depende de) User
            └── (Depende de) Product
    ```

---

### **5. EJEMPLOS DE ESCENARIOS COMPLEJOS**

#### **Escenario 1: Lanzar un capítulo semanal de pago.**
*   **Paso a paso actual:**
    1.  Crear un `Product` en la tienda: "Acceso Capítulo 10". Anotar su ID (requiere acceso a BBDD).
    2.  Crear el `NarrativeFragment` del Capítulo 10. Marcarlo como bloqueado.
    3.  Pegar el ID del producto cuando el bot lo pida.
    4.  Una semana después, repetir los 3 pasos para el Capítulo 11 con un nuevo producto.
*   **Complejidad:** Proceso repetitivo y manual. El riesgo de pegar el ID incorrecto aumenta con cada capítulo. La tienda se llenará de productos "llave" de un solo uso.
*   **Entidades:** `Product`, `NarrativeFragment`.
*   **Automatización ideal:** Un panel donde se sube el contenido del capítulo, se marca como "de pago", y el sistema automáticamente:
    1.  Crea un producto asociado con un nombre estándar ("Pase Capítulo 10").
    2.  Vincula el ID internamente sin intervención del administrador.

#### **Escenario 2: Crear una misión secundaria que regala un objeto.**
*   **Paso a paso actual:**
    1.  Crear el `Product` que será la recompensa (e.g., "Medalla del Valor"). Anotar su ID.
    2.  Crear la secuencia de `NarrativeFragment` que componen la misión. Anotar el ID del último fragmento.
    3.  Pedir a un desarrollador que edite `narrative_handler.py`.
    4.  El desarrollador añade: `if fragment.id == 'ID_ULTIMO_FRAGMENTO': dar_recompensa(user_id, 'ID_PRODUCTO_RECOMPENSA')`.
    5.  Desplegar los cambios del bot.
*   **Complejidad:** Requiere intervención técnica para una tarea de contenido. Lento, arriesgado y nada flexible.
*   **Entidades:** `Product`, `NarrativeFragment`, lógica de `Trigger/Reward`.
*   **Automatización ideal:** En el panel, al crear el último fragmento de la misión, habría una sección "Recompensas al finalizar" -> "Añadir Recompensa" -> "Tipo: Producto" -> (Seleccionar "Medalla del Valor" de una lista).

#### **Escenario 3: Configurar un regalo de bienvenida para nuevos usuarios.**
*   **Paso a paso actual:**
    1.  Crear el `Product` a regalar (e.g., "Kit de Bienvenida"). Anotar su ID.
    2.  Un desarrollador edita el `handler` `start.py`.
    3.  En la función que crea un nuevo usuario, añade una llamada a `add_item_to_inventory(new_user_id, 'ID_KIT_BIENVENIDA')`.
    4.  Desplegar los cambios.
*   **Complejidad:** Idéntica al escenario 2. Una decisión de negocio (qué regalar) requiere una modificación de código.
*   **Entidades:** `User`, `Product`, `InventoryItem`.
*   **Automatización ideal:** Un panel de "Automatizaciones" -> "Trigger: Nuevo Usuario" -> "Acción: Entregar Producto" -> (Seleccionar "Kit de Bienvenida" de una lista).

---

### **6. PROBLEMAS DETECTADOS EN EL SISTEMA ACTUAL**

1.  **Complejidad Innecesaria y Riesgo de Errores:** La dependencia de copiar y pegar IDs entre diferentes módulos es la mayor fuente de complejidad y errores. No hay integridad referencial a nivel de interfaz de admin.
2.  **Falta de Consistencia (Lógica Aislada):** La lógica de negocio está peligrosamente fragmentada. Parte está en los `handlers` de admin, parte en los `handlers` de usuario, parte en `scripts` y otra parte crucial (triggers/recompensas) directamente en el código fuente, inaccesible para un administrador.
3.  **Falta de Propagación Automática:** Crear un producto no sugiere vincularlo a un fragmento. Crear un fragmento no permite crear el producto necesario "al vuelo". Son flujos de trabajo unidireccionales y desconectados.
4.  **Cuellos de Botella:** Cualquier cambio en la lógica de recompensas, triggers o journeys requiere un desarrollador y un nuevo despliegue. Esto es un cuello de botella operativo enorme.
5.  **Escalabilidad Limitada:** El sistema actual no puede escalar en complejidad. Añadir más misiones con recompensas, más journeys o más tipos de condiciones requerirá cada vez más código "hardcodeado", haciendo el sistema progresivamente más frágil y difícil de mantener.
6.  **Lógica Duplicada:** Es probable que la lógica para otorgar recompensas esté copiada en varios `handlers` en lugar de centralizada en un único servicio de recompensas.

---

### **7. OTROS COMPONENTES RELEVANTES**

*   **Midivan / Emotional Models:** Se han detectado modelos como `emotional_models.py` y `midivan_models.py`. Parecen ser sistemas paralelos o en desarrollo para rastrear el estado emocional del usuario o gestionar otro tipo de interacciones. Actualmente, no parecen estar integrados en los flujos de administración principales, pero un panel unificado debería considerar espacios para gestionar estas características en el futuro.
*   **Alembic (Migraciones):** El uso de Alembic es una buena práctica. Asegura que los cambios en los modelos de la base de datos se pueden aplicar de forma controlada. El panel de administración deberá respetar y utilizar los modelos existentes para no entrar en conflicto con el esquema de la BBDD.

---
**Conclusión Final:**

El sistema actual es funcional pero frágil y altamente dependiente de la intervención manual y técnica. La creación de un panel de administración web unificado no es solo una mejora, sino una necesidad crítica para la estabilidad, escalabilidad y agilidad operativa del bot.

El enfoque principal del nuevo panel debe ser:
1.  **Abstraer los IDs:** El usuario debe seleccionar entidades de listas desplegables, no pegar IDs.
2.  **Unificar Flujos:** Permitir crear un producto "llave" desde la misma pantalla de creación de un fragmento bloqueado.
3.  **Centralizar la Lógica de Negocio:** Crear una interfaz para definir Triggers y Recompensas sin tocar el código.
4.  **Proporcionar Visibilidad:** Ofrecer un dashboard que muestre las conexiones: qué pr
