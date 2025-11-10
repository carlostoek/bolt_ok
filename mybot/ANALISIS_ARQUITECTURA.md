# Análisis de Arquitectura del Bot de Telegram

Este documento detalla la arquitectura, módulos y flujos de datos del bot de Telegram, basado en el análisis del código fuente.

## 1. Arquitectura General

### Stack Tecnológico
- **Lenguaje:** Python 3
- **Framework de Bot:** `aiogram` para la interacción asíncrona con la API de Telegram.
- **Base de Datos:** SQLite, gestionada a través del ORM `SQLAlchemy`. Se evidencia en `database/setup.py`.
- **Manejo de Migraciones:** `alembic` está configurado (`alembic.ini`), lo que indica un manejo estructurado de los cambios en el schema de la base de datos.

### Estructura de Directorios y Organización del Código
El proyecto sigue una estructura modular y limpia, separando responsabilidades:
- `handlers/`: Contiene la lógica de presentación, manejando los comandos y callbacks de Telegram. Es el punto de entrada para las interacciones del usuario.
- `services/`: Contiene la lógica de negocio. Los servicios orquestan las operaciones, interactuando con la base de datos y otros servicios.
- `database/`: Define los modelos de datos (`models.py`, `narrative_models.py`, etc.) con SQLAlchemy, y la configuración de la conexión.
- `keyboards/`: Define los teclados interactivos que se muestran al usuario.
- `config/`: Almacena archivos de configuración estáticos, como schemas JSON.
- `bot.py`: Punto de entrada de la aplicación que inicializa el bot, el dispatcher y registra los routers de los diferentes módulos.

### Dependencias Principales
El archivo `requirements.txt` revela las siguientes dependencias clave:
- `aiogram`: Framework principal del bot.
- `sqlalchemy`: ORM para la interacción con la base de datos.
- `alembic`: Para migraciones de la base de datos.
- `asyncpg` (potencialmente): Aunque se usa SQLite, la presencia de este driver sugiere que podría estar preparado para PostgreSQL.

## 2. Módulo de Narrativa

### Modelo de Datos de Fragmentos
La narrativa se estructura principalmente en el archivo `database/narrative_models.py`.

- **`StoryFragment`**: Representa un nodo en la historia.
  - `key`: Un identificador **único de tipo string** (ej: `diana_intro_1`) que es la clave principal para la navegación.
  - `text`: El contenido del fragmento.
  - `character`: Personaje que habla (Lucien o Diana).
  - `auto_next_fragment_key`: Si no es nulo, la historia avanza automáticamente a este fragmento sin mostrar decisiones.
```python
# extraído de database/narrative_models.py
class StoryFragment(Base):
    __tablename__ = 'story_fragments'

    id = Column(Integer, primary_key=True)
    key = Column(String(50), unique=True, nullable=False)
    text = Column(Text, nullable=False)
    # ... otros campos ...
    auto_next_fragment_key = Column(String(50), nullable=True)
    # ...
```

### Almacenamiento de Decisiones y Consecuencias
- **`NarrativeChoice`**: Representa una opción que el usuario puede tomar. Crucialmente, vincula un fragmento de origen con uno de destino a través de claves de string.
  - `source_fragment_id`: El ID del fragmento donde se muestra esta opción.
  - `destination_fragment_key`: La **clave string** del fragmento al que se navegará si se elige esta opción.
- **`UserNarrativeState`**: Almacena el progreso del usuario.
  - `current_fragment_key`: La clave del fragmento actual del usuario.
  - `choices_made`: Un campo JSON que almacena un historial de las decisiones tomadas.

```python
# extraído de database/narrative_models.py
class NarrativeChoice(Base):
    __tablename__ = 'narrative_choices'

    id = Column(Integer, primary_key=True)
    source_fragment_id = Column(Integer, ForeignKey('story_fragments.id'), nullable=False)
    destination_fragment_key = Column(String(50), nullable=False)
    text = Column(String, nullable=False)
    # ...
```
### Sistema de Bloqueo/Desbloqueo de Contenido
El acceso a fragmentos y decisiones está controlado por requisitos directamente en los modelos.
- `StoryFragment.min_besitos`: Requiere una cantidad mínima de puntos ("besitos") para acceder al fragmento.
- `StoryFragment.required_role`: Requiere un rol de usuario específico (ej: `vip`).
- `NarrativeChoice.required_besitos` y `NarrativeChoice.required_role`: Lo mismo, pero aplicado a una decisión específica.

El `NarrativeService` es responsable de validar estos requisitos antes de mostrar el contenido.

### Relaciones entre Fragmentos (Árbol de Decisiones)
La estructura es un grafo dirigido. Cada `StoryFragment` es un nodo. Las aristas son las `NarrativeChoice` que conectan un `source_fragment_id` con un `destination_fragment_key`. La navegación se basa en las claves de string, lo que permite flexibilidad para definir y modificar la narrativa sin romper referencias de IDs numéricos.

### Identificadores Únicos
- **Fragmentos:** `key` (String, ej: `lucien_despertar_3`). Este es el identificador de negocio.
- **Decisiones:** `id` (Integer, autoincremental).
- **Otros Modelos (Misiones, Pistas):** `code_name` (String) o `id` (String).

## 3. Módulo de Gamificación

### Sistema de Puntos
- Los puntos se denominan "besitos" dentro del sistema.
- Se almacenan en el modelo `User`, en la columna `points`.
- **Otorgamiento:** Los puntos se conceden principalmente a través de:
  - `StoryFragment.reward_besitos`: Al completar un fragmento narrativo.
  - `Mission.reward_points`: Al completar una misión.
  - Reacciones a publicaciones en canales (configurado en `Channel.reaction_points`).

### Estructura de Recompensas y Misiones
El archivo `database/models.py` define un sistema de gamificación robusto:
- **`Mission`**: Define una tarea a realizar (ej: "reacciona 5 veces"). Tiene un `type` (`one_time`, `daily`), `reward_points`, y puede desbloquear una pista (`unlocks_lore_piece_code`).
- **`UserMissionEntry`**: Tabla pivot que registra el progreso de un usuario en una misión.
- **`Achievement`**: Logros que se desbloquean bajo ciertas condiciones.
- **`Reward`**: Recompensas por alcanzar hitos de puntos.
- **`LorePiece`**: Pistas o piezas de historia coleccionables que se pueden desbloquear.

### Sistema de Widgets
El término "widget" no se usa explícitamente. Sin embargo, la interfaz de gamificación se construye a través de teclados interactivos (`InlineKeyboard`) definidos en `keyboards/` que se presentan en los `handlers/`. Por ejemplo, `handlers/missions_handler.py` muestra la lista de misiones con botones para interactuar.

### Integración con Narrativa
La gamificación y la narrativa están estrechamente ligadas:
- **Misiones que Desbloquean Pistas:** `Mission.unlocks_lore_piece_code` crea una relación directa donde completar una misión otorga una `LorePiece`.
- **Narrativa que Desbloquea Logros:** `StoryFragment.unlocks_achievement_id` permite que avanzar en la historia otorgue `Achievement`.
- **Niveles que Desbloquean Pistas:** El modelo `Level` tiene un campo `unlocks_lore_piece_code`.

## 4. Módulo de Administración de Canales

### Estados de Usuario
- **`User.role`**: Columna clave que define el estado del usuario. Los valores observados son `free` y `vip`.
- **`User.vip_expires_at`**: Fecha de expiración para el estado VIP.
- **`VipSubscription`** y **`VipGrant`**: Modelos dedicados para gestionar las suscripciones VIP y los accesos gratuitos otorgados, lo que permite una auditoría completa.

### Sistema de Reacciones y Eventos
- **`Channel.reactions`**: Un campo JSON que lista los emojis permitidos para reaccionar en un canal.
- **`Channel.reaction_points`**: Un JSON que mapea cada emoji a una cantidad de puntos a otorgar.
- **`Event`**: Un modelo para definir eventos especiales (ej: "doble de puntos por reacciones") con un multiplicador y fechas de inicio/fin.

### Permisos y Roles
- **Admin:** El campo booleano `User.is_admin` otorga acceso a paneles de administración. El handler `handlers/start.py` diferencia entre usuarios normales y administradores para mostrar menús distintos.
- **Roles (VIP/Free):** Múltiples servicios y handlers verifican el `user.role` para restringir el acceso a contenido, como se ve en los campos `required_role` de los modelos de narrativa y tienda.

## 5. Tienda

### Modelo de Productos
- **`ShopItem`**: El modelo central de la tienda, definido en `database/models.py`. Contiene toda la información de un producto.
  - `price`: Costo en "besitos".
  - `is_vip_only`: Booleano para restringir la compra a usuarios VIP.
  - `stock_limit`: Para productos con existencias limitadas.
  - `max_purchases_per_user`: Límite de compras por usuario.
  - `unlock_requirements`: Un campo JSON para definir condiciones complejas de desbloqueo.

```python
# extraído de database/models.py
class ShopItem(Base):
    __tablename__ = "shop_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    price = Column(Integer, nullable=False)  # Price in besitos
    is_vip_only = Column(Boolean, default=False)
    unlocks_lore_piece_id = Column(Integer, ForeignKey("lore_pieces.id"), nullable=True)
    unlocks_fragment_key = Column(String(50), nullable=True)  # Key of StoryFragment
    stock_limit = Column(Integer, nullable=True)
    # ...
```

### Tipos de Productos
Los productos son agnósticos y su función se define por lo que desbloquean:
- **Desbloqueo de Fragmentos:** `ShopItem.unlocks_fragment_key` vincula un producto a un fragmento narrativo, permitiendo comprar acceso a ramas de la historia.
- **Desbloqueo de Pistas:** `ShopItem.unlocks_lore_piece_id` vincula un producto a una `LorePiece`.
- **Desbloqueo de Estado VIP:** No se observa un campo directo, pero podría manejarse a través de un producto que otorga una recompensa de tipo `vip_access`.

### Sistema de Compra y Validación
El flujo se maneja en `handlers/shop_handlers.py` y `services/shop_service.py`:
1. El usuario selecciona un producto.
2. El sistema verifica si el usuario cumple los requisitos (puntos, rol, stock, etc.).
3. Si la validación es exitosa, se crea un registro en la tabla `UserPurchase`.
4. Se descuentan los puntos del `User.points`.
5. Se otorga el contenido desbloqueado (se crea un `UserLorePiece` o se actualiza el `UserNarrativeState`).
El `narrative_handler.py` contiene lógica de "retorno de la tienda" (`return_from_shop`) para manejar decisiones narrativas que requerían una compra, demostrando una integración profunda.

### Referencias Cruzadas
- **`ShopItem.unlocks_fragment_key`**: Referencia de **String** a `StoryFragment.key`.
- **`ShopItem.unlocks_lore_piece_id`**: Referencia de **Integer** (clave foránea) a `LorePiece.id`.

## 6. Configuración Actual

### Archivos de Configuración
- `config/narrative_schema.json`: Un schema JSON que valida la estructura de los archivos de configuración de narrativa. Esto es una excelente práctica para mantener la consistencia.
- `config/decision_requirements.json`: Un archivo JSON simple que parece mapear IDs de decisión a nombres de items requeridos (ej: "Diario Secreto").
- La base de datos misma actúa como una fuente de configuración para misiones, productos de la tienda, etc., que se gestionan probablemente a través de un panel de admin.

### Formato de Datos
- **JSON:** Es el formato principal para la configuración estática y para campos flexibles en la base de datos.
- **Base de Datos:** La mayoría de las entidades (misiones, productos) se definen como registros en la base de datos, lo que permite una gestión dinámica.

### Proceso de Creación/Vinculación de Elementos
El flujo de trabajo parece ser una combinación de:
1. **Configuración estática:** Definir la estructura base y ciertos elementos en archivos JSON.
2. **Gestión dinámica:** Utilizar paneles de administración (inferido por la existencia de `handlers/admin/`) para crear y modificar misiones, productos y fragmentos narrativos directamente en la base de datos.
La vinculación se realiza consistentemente a través de identificadores de string (`key`, `code_name`) o IDs numéricos.

### Pain Points Identificados
- **Configuración descentralizada:** La configuración reside en múltiples lugares: archivos JSON, la base de datos y valores hardcodeados en el código (ej: en teclados). Esto puede dificultar la gestión y el seguimiento de todos los parámetros del sistema.
- **Confianza en IDs numéricos:** Aunque se usan claves de string en la narrativa, otros módulos todavía dependen de IDs numéricos autoincrementales como claves foráneas, lo que puede ser más frágil al migrar datos entre entornos.

## 7. APIs y Endpoints

### Comandos del Bot Expuestos
Basado en los `handlers`, se identifican los siguientes comandos para el usuario:
- `/start`: Inicia la interacción y muestra el menú principal. (en `handlers/start.py`)
- `/historia`: Inicia o continúa la narrativa. (en `handlers/narrative_handler.py`)
- `/mi_historia`: Muestra estadísticas del progreso narrativo. (en `handlers/narrative_handler.py`)
Además de estos, el bot funciona principalmente a través de callbacks de botones (`CallbackQuery`).

### API REST/GraphQL
No se ha encontrado evidencia de una API REST o GraphQL expuesta. La comunicación es interna entre los módulos de Python o directa con la API de Telegram.

### Webhooks de Telegram
El framework `aiogram` puede operar tanto en modo `polling` como `webhook`. El archivo `bot.py` es donde se realizaría esta configuración. Aunque no se especifica el modo, una aplicación en producción típicamente usaría webhooks para mayor eficiencia.

## 8. Interconexiones Críticas

### Mapa de Dependencias
- **Orquestador Principal:** El `CoordinadorCentral` (mencionado en el análisis del código) actúa como una fachada que orquesta flujos complejos entre módulos, desacoplando los servicios entre sí.
- **Flujo:** `Handlers` reciben input -> llaman a `Services` -> `Services` ejecutan la lógica de negocio, usando los `Models` de la base de datos para persistir los cambios.

### Flujos de Datos Clave
- **Usuario completa un fragmento narrativo:**
  1. `narrative_handler` recibe el callback de la decisión.
  2. Llama a `NarrativeService` para procesar la decisión.
  3. `NarrativeService` valida requisitos, actualiza `UserNarrativeState.current_fragment_key`.
  4. Otorga `reward_besitos` actualizando `User.points`.
  5. Desbloquea un `Achievement` si `unlocks_achievement_id` está presente.
  6. Devuelve el siguiente `StoryFragment` al handler para ser mostrado.

- **Usuario reacciona a una publicación:**
  1. Un `reaction_handler` (no mostrado, pero inferido) captura el evento.
  2. Obtiene los puntos para esa reacción de `Channel.reaction_points`.
  3. Actualiza `User.points`.
  4. Actualiza el progreso de cualquier misión de tipo "reacción" en `UserMissionEntry`.

- **Usuario compra un producto:**
  1. `shop_handlers` recibe el callback de compra.
  2. Llama a `ShopService` para ejecutar la compra.
  3. `ShopService` verifica los puntos del usuario y otros requisitos.
  4. Crea un registro en `UserPurchase`.
  5. Deduce los puntos de `User.points`.
  6. Si `unlocks_lore_piece_id` está presente, crea un registro en `UserLorePiece`.
  7. Si `unlocks_fragment_key` está presente, actualiza el `UserNarrativeState` o un campo similar para dar acceso.
  8. El `narrative_handler` tiene lógica para re-evaluar una decisión pendiente después de que el usuario regresa de la tienda.

- **Usuario completa una misión:**
  1. Un evento (ej: enviar un mensaje, reaccionar) dispara una verificación en `MissionService`.
  2. `MissionService` actualiza el `progress_value` en `UserMissionEntry`.
  3. Si el progreso alcanza `Mission.target_value`, marca la misión como completada.
  4. Otorga los `reward_points` a `User.points`.
  5. Si `unlocks_lore_piece_code` está presente, crea un registro en `UserLorePiece`.