# Panel de Administración del Bot - Estructura del Proyecto

## 📁 Estructura de Carpetas

```
app/
├── main.py                     # Punto de entrada de FastAPI
├── core/
│   ├── __init__.py
│   └── config.py              # Configuración con pydantic-settings
├── database/
│   ├── __init__.py
│   └── session.py             # SQLAlchemy AsyncSession + engine
├── models/                     # Modelos ORM (SQLAlchemy)
│   ├── __init__.py
│   ├── narrative.py           # StoryFragment, NarrativeChoice
│   └── shop.py                # ShopItem
├── schemas/                    # Esquemas DTO (Pydantic V2)
│   ├── __init__.py
│   ├── narrative.py           # FragmentCreate, ChoiceCreateNested, etc.
│   └── shop.py                # ProductCreate, ProductCreateNested, etc.
├── services/                   # Lógica de negocio
│   └── __init__.py
│       └── [PENDIENTE: nested_creation_service.py]
└── api/
    └── v1/
        ├── __init__.py
        └── endpoints/
            ├── __init__.py
            └── [PENDIENTE: narrative.py, shop.py]
```

## 🎯 Arquitectura Implementada

### Capa 1: Configuración (`core/`)
- **config.py**: Gestión centralizada de variables de entorno usando `pydantic-settings`
- Variables de BD, API, seguridad, CORS
- Singleton `settings` disponible globalmente

### Capa 2: Base de Datos (`database/`)
- **session.py**: Configuración de SQLAlchemy Async
  - `Base`: Clase declarativa base
  - `engine`: Async engine con pool de conexiones
  - `AsyncSessionLocal`: Factory para crear sesiones
  - `get_db()`: Dependency para FastAPI endpoints
  - `init_db()`: Crear todas las tablas
  - `close_db()`: Cerrar conexiones al apagar

### Capa 3: Modelos ORM (`models/`)

#### narrative.py
```python
class StoryFragment(Base):
    id, key, text, image_url
    min_besitos, required_role, reward_besitos
    auto_next_fragment_key
    choices (relationship → NarrativeChoice)
    unlocking_products (relationship → ShopItem)

class NarrativeChoice(Base):
    id, source_fragment_id, destination_fragment_key
    text, required_besitos, required_role, is_hidden
    source_fragment (relationship → StoryFragment)
```

#### shop.py
```python
class ShopItem(Base):
    id, name, description
    price, is_vip_only
    unlocks_fragment_key
    stock_limit, max_purchases_per_user
    unlocks_fragment (relationship → StoryFragment)
```

**Relaciones Implementadas:**
- `StoryFragment.choices` ↔ `NarrativeChoice.source_fragment`
- `StoryFragment.unlocking_products` ↔ `ShopItem.unlocks_fragment`
- Uso de `key` (string) para referencias en lugar de IDs

### Capa 4: Esquemas Pydantic V2 (`schemas/`)

#### shop.py
```python
ProductCreateNested      # Para crear producto inline (sin ID)
ProductCreate            # Creación estándar con FK opcional
ProductUpdate            # Actualización parcial
ProductResponse          # Respuesta de lectura
```

#### narrative.py
```python
# Nested Creation Schemas
FragmentCreateNested     # Para crear fragmento inline
ChoiceCreateNested       # Para crear decisión inline
                         # Soporta destination_fragment_key O destination_fragment

FragmentCreate           # Schema principal de creación atómica
                         # Soporta unlock_product (nested)
                         # Soporta choices[] (nested con destinos nested)

# Standard Schemas
FragmentUpdate           # Actualización de fragmento
FragmentResponse         # Respuesta de lectura
ChoiceResponse           # Respuesta de decisión
FragmentCreateResponse   # Respuesta de creación con resumen
```

**Características Clave:**
- ✅ Uso de `ForwardRef` para resolver referencias circulares
- ✅ `model_rebuild()` al final para actualizar refs
- ✅ Validadores personalizados con `@field_validator`
- ✅ `ConfigDict(from_attributes=True)` para compatibilidad con ORM
- ✅ Soporte completo para Atomic Nested Creation

## 🔧 Configuración de Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/botdb

# API
API_V1_PREFIX=/api/v1
PROJECT_NAME=Bot Admin Panel
DEBUG=false

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# SQLAlchemy
POOL_SIZE=5
MAX_OVERFLOW=10
ECHO_SQL=false
```

## 🚀 Instalación y Ejecución

### 1. Instalar Dependencias

```bash
pip install fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg pydantic pydantic-settings
```

### 2. Ejecutar la Aplicación

```bash
# Desarrollo (con hot-reload)
python app/main.py

# O usando uvicorn directamente
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Verificar que Funciona

```bash
curl http://localhost:8000/
# {"message":"Bot Admin Panel API","version":"1.0.0","status":"running"}

curl http://localhost:8000/health
# {"status":"healthy"}
```

## 📊 Patrón de Creación Anidada (Atomic Nested Creation)

### Ejemplo de Uso

**Payload JSON:**
```json
POST /api/v1/fragments
{
  "key": "CAP_FINAL",
  "text": "Entrada al castillo oscuro...",
  "reward_besitos": 50,

  "unlock_product": {
    "name": "Llave Maestra",
    "price": 100,
    "is_vip_only": false
  },

  "choices": [
    {
      "text": "Entrar al salón del trono",
      "destination_fragment": {
        "key": "SALON_TRONO",
        "text": "El rey te espera...",
        "reward_besitos": 20
      }
    }
  ]
}
```

**Resultado:**
- ✅ 1 producto creado (ID: 42, "Llave Maestra")
- ✅ 1 fragmento principal creado (ID: 10, "CAP_FINAL")
- ✅ Producto vinculado al fragmento (`unlocks_fragment_key = "CAP_FINAL"`)
- ✅ 1 fragmento destino creado (ID: 11, "SALON_TRONO")
- ✅ 1 decisión creada vinculando CAP_FINAL → SALON_TRONO

**Todo en una transacción atómica.**

## 🎯 Ventajas del Diseño

### 1. Modularidad
- Cada capa tiene una responsabilidad clara
- Fácil de testear y mantener
- Separación entre ORM y DTOs

### 2. Type Safety
- Pydantic V2 valida automáticamente los datos
- SQLAlchemy ORM evita SQL injection
- Type hints en todo el código

### 3. Async/Await
- No bloquea el event loop
- Escala bien con múltiples peticiones concurrentes
- Compatible con PostgreSQL async (asyncpg)

### 4. Atomic Nested Creation
- Elimina 7 pasos manuales → 1 petición HTTP
- Sin copy-paste de IDs
- Sin errores de vinculación
- Transacción atómica (todo o nada)

### 5. Clean Architecture
- Dependencias apuntan hacia adentro
- Fácil migrar de PostgreSQL a otro DB
- Services desacoplados de FastAPI
- Schemas desacoplados de Models

## 📝 Próximos Pasos

### Fase 1: Servicios de Negocio
```
app/services/nested_creation_service.py
```
- Implementar lógica de creación anidada
- Inspirado en la POC (`poc_nested_creation.py`)
- Uso de `flush()` para obtener IDs sin commit
- Único `commit()` al final

### Fase 2: Endpoints de API
```
app/api/v1/endpoints/narrative.py
app/api/v1/endpoints/shop.py
```
- `POST /api/v1/fragments` - Creación anidada
- `GET /api/v1/fragments/{key}` - Obtener fragmento
- `PUT /api/v1/fragments/{key}` - Actualizar fragmento
- `DELETE /api/v1/fragments/{key}` - Eliminar fragmento
- CRUD completo para productos

### Fase 3: Migraciones
```
alembic init migrations
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

### Fase 4: Testing
```
tests/
├── test_nested_creation.py
├── test_narrative_endpoints.py
└── test_shop_endpoints.py
```

### Fase 5: Frontend
- Next.js con formularios para nested creation
- Componente `<NestedProductSelector />`
- Componente `<NestedChoicesEditor />`

## 🔗 Referencias

- **POC Validada:** `/home/azureuser/repos/bolt_ok/mybot/poc_nested_creation.py`
- **Reporte de Resultados:** `/home/azureuser/repos/bolt_ok/mybot/docs/atomic_nested_results.md`
- **Arquitectura Actual:** `/home/azureuser/repos/bolt_ok/mybot/docs/arquitectura_actual.md`

## 📦 Dependencias del Proyecto

```requirements.txt
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy[asyncio]>=2.0.0
asyncpg>=0.29.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
alembic>=1.13.0
python-dotenv>=1.0.0
```

## ✅ Estado Actual

- ✅ Estructura de carpetas creada
- ✅ Configuración implementada
- ✅ Database session configurada
- ✅ Modelos ORM definidos
- ✅ Esquemas Pydantic V2 implementados
- ✅ Relaciones bidireccionales configuradas
- ✅ Forward references resueltas
- ✅ Main.py con lifespan events
- ⏳ **Pendiente:** Servicios de negocio
- ⏳ **Pendiente:** Endpoints de API
- ⏳ **Pendiente:** Tests

## 🎓 Conceptos Clave

### `flush()` vs `commit()`
```python
# flush() - Genera IDs sin commit
await session.flush()
product_id = product.id  # ✅ ID disponible

# commit() - Persiste en BD
await session.commit()
```

### Nested Creation
```python
# Cliente envía esto:
{
    "fragment": {...},
    "unlock_product": {...}  # Nested
}

# Servidor hace esto:
1. Crear producto → flush() → obtener ID
2. Crear fragmento con product_id
3. commit() todo junto
```

### Rollback Automático
```python
try:
    # ... operaciones
    await session.commit()
except Exception:
    await session.rollback()  # ✅ Automático en get_db()
    raise
```

---

**Listo para continuar con la implementación de servicios y endpoints.**
