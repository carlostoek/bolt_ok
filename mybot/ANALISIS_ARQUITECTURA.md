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
