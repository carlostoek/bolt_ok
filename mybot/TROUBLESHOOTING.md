# Guía de Solución de Problemas

## Problemas Comunes con Tests Asíncronos

### 1. `'async_generator' object has no attribute 'add'`

**Problema:**
Este error ocurre cuando se intenta usar una fixture asíncrona incorrectamente.

**Solución:**
1. Verificar que el archivo `pytest.ini` tenga la configuración correcta:
   ```ini
   [tool:pytest]
   asyncio_mode = auto
   ```

2. Asegurarse de que las fixtures asíncronas estén definidas correctamente en `conftest.py`:
   ```python
   @pytest.fixture
   async def session(session_factory):
       async with session_factory() as session:
           yield session
   ```

3. Usar el decorador `@pytest.mark.asyncio` en los tests que requieren fixtures asíncronas:
   ```python
   @pytest.mark.asyncio
   async def test_example(session):
       # test code
   ```

### 2. `coroutine 'session_factory' was never awaited`

**Problema:**
Este error ocurre cuando se intenta usar una coroutine sin await.

**Solución:**
1. Asegurarse de usar `await` cuando se llama a funciones asíncronas:
   ```python
   # Correcto
   session_factory = await get_session()
   
   # Incorrecto
   session_factory = get_session()
   ```

2. Verificar que las fixtures estén correctamente definidas:
   ```python
   @pytest.fixture
   async def session_factory(test_engine):
       return async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
   ```

### 3. Warnings sobre fixtures asíncronos en modo estricto

**Problema:**
Pytest muestra warnings sobre el uso de fixtures asíncronas.

**Solución:**
1. Configurar el modo asyncio en `pytest.ini`:
   ```ini
   [tool:pytest]
   asyncio_mode = auto
   ```

2. O usar el modo estricto si se prefiere:
   ```ini
   [tool:pytest]
   asyncio_mode = strict
   ```
   Y entonces decorar explícitamente los tests:
   ```python
   @pytest.mark.asyncio
   async def test_example(session):
       # test code
   ```

## Problemas con Dependencias

### 1. Versiones incompatibles de SQLAlchemy

**Problema:**
Errores relacionados con el uso de sesiones asíncronas.

**Solución:**
1. Asegurarse de tener SQLAlchemy 2.0+:
   ```bash
   poetry add sqlalchemy@^2.0.0
   ```

2. Verificar el uso correcto de sesiones asíncronas:
   ```python
   from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
   
   # Crear engine asíncrono
   engine = create_async_engine("sqlite+aiosqlite:///test.db")
   
   # Crear session factory
   session_factory = async_sessionmaker(engine, class_=AsyncSession)
   
   # Usar la sesión
   async with session_factory() as session:
       # operaciones con la base de datos
   ```

### 2. Problemas con pytest-asyncio

**Problema:**
Los tests no se ejecutan correctamente o se comportan de manera inesperada.

**Solución:**
1. Verificar que pytest-asyncio esté instalado:
   ```bash
   poetry add --group dev pytest-asyncio@^0.21.0
   ```

2. Usar la configuración correcta en `pyproject.toml`:
   ```toml
   [tool.pytest.ini_options]
   asyncio_mode = "auto"
   ```

## Problemas con la Base de Datos

### 1. Base de datos no se crea correctamente

**Problema:**
Errores al ejecutar tests debido a que las tablas no existen.

**Solución:**
1. Verificar que el código de inicialización de la base de datos esté correcto:
   ```python
   async with engine.begin() as conn:
       await conn.run_sync(Base.metadata.create_all)
   ```

2. Asegurarse de que los modelos estén correctamente definidos y registrados en `Base`.

### 2. Conexiones abiertas que causan bloqueos

**Problema:**
Las pruebas fallan intermitentemente debido a conexiones no cerradas.

**Solución:**
1. Usar context managers para manejar sesiones:
   ```python
   @pytest.fixture
   async def session(session_factory):
       async with session_factory() as session:
           yield session
       # La sesión se cierra automáticamente al salir del contexto
   ```

2. Verificar que en el código de la aplicación también se usen context managers:
   ```python
   async with session_factory() as session:
       # operaciones con la base de datos
       await session.commit()
   # La sesión se cierra automáticamente
   ```

## Problemas Específicos con Tests Asíncronos

### TypeError: 'coroutine' object does not support the asynchronous context manager protocol

**Problema:** Este error ocurre al intentar usar un objeto mock en un context manager asíncrono, como cuando usamos `async with session.begin()` pero `session` es un `AsyncMock`.

**Solución:** Configurar correctamente el AsyncMock para que soporte el protocolo de context manager asíncrono:

```python
# Configuración correcta de AsyncMock para context manager asíncrono
session_mock = AsyncMock()
mock_context = AsyncMock()
mock_context.__aenter__.return_value = session_mock
session_mock.begin.return_value = mock_context

# Ahora este código funcionará
async with session_mock.begin():
    # Código dentro del context manager
```

### RuntimeWarning: coroutine was never awaited

**Problema:** Este warning aparece cuando hay coroutines que no se esperan con `await`.

**Solución:**

1. Asegúrate de usar `await` para todas las funciones asíncronas:

```python
# Incorrecto
session_factory()

# Correcto
await session_factory()
```

2. Si estás usando mocks para funciones asíncronas, configura correctamente los valores de retorno:

```python
mock_function = AsyncMock()
mock_function.return_value = "valor"  # No return_value=await algo()
```

## Problemas en Entorno Termux (Android)

### 1. Permisos insuficientes

**Problema:**
Errores al ejecutar scripts o crear archivos.

**Solución:**
1. Asegurarse de que Termux tenga permisos de almacenamiento:
   ```bash
   termux-setup-storage
   ```

2. Verificar permisos de los scripts:
   ```bash
   chmod +x setup.sh
   chmod +x test.sh
   chmod +x dev.sh
   ```

### 2. Dependencias del sistema faltantes

**Problema:**
Errores al instalar paquetes de Python que requieren compilación.

**Solución:**
1. Instalar paquetes del sistema necesarios:
   ```bash
   pkg install python python-pip git
   pkg install clang libffi openssl
   ```

2. Para paquetes que requieren compilación, usar versiones precompiladas:
   ```bash
   # En lugar de compilar desde source
   poetry add psycopg2-binary  # En lugar de psycopg2
   ```

## Problemas de Concurrencia

### 1. Race conditions en tests

**Problema:**
Tests que fallan intermitentemente debido a condiciones de carrera.

**Solución:**
1. Aislar cada test usando fixtures con scope adecuado:
   ```python
   @pytest.fixture
   async def session(session_factory):
       # Cada test obtiene una sesión nueva
       async with session_factory() as session:
           yield session
   ```

2. Usar bases de datos en memoria para tests:
   ```python
   @pytest.fixture(scope="session")
   async def test_engine():
       engine = create_async_engine(
           "sqlite+aiosqlite:///:memory:",
           poolclass=StaticPool,
           connect_args={"check_same_thread": False}
       )
       # ...
   ```

### 2. Tests que se afectan mutuamente

**Problema:**
El estado de un test afecta la ejecución de otro.

**Solución:**
1. Asegurarse de que cada test limpie después de sí mismo:
   ```python
   @pytest.fixture(autouse=True)
   async def clean_database(session):
       # Limpiar tablas antes de cada test
       for table in reversed(Base.metadata.sorted_tables):
           await session.execute(table.delete())
       await session.commit()
       yield
       # Limpiar después del test si es necesario
   ```

2. Usar transacciones que se revierten:
   ```python
   @pytest.fixture
   async def transactional_session(session_factory):
       async with session_factory() as session:
           async with session.begin():  # Iniciar transacción
               yield session
           # La transacción se revierte automáticamente al salir
   ```

## Problemas con CI/CD

### 1. Tests que pasan localmente pero fallan en CI

**Problema:**
Diferencias entre el entorno local y el de CI.

**Solución:**
1. Asegurarse de que ambos entornos usen las mismas versiones de dependencias:
   ```bash
   poetry export -f requirements.txt --output requirements.txt
   ```

2. Verificar que el entorno de CI tenga las mismas dependencias del sistema.

3. Usar contenedores Docker para garantizar consistencia:
   ```dockerfile
   FROM python:3.10
   RUN pip install poetry
   COPY poetry.lock pyproject.toml ./
   RUN poetry install
   COPY . .
   CMD ["poetry", "run", "pytest"]
   ```

## Verificación del Entorno

### Comandos de diagnóstico

1. Verificar versiones instaladas:
   ```bash
   poetry run python --version
   poetry run pytest --version
   poetry run python -c "import sqlalchemy; print(sqlalchemy.__version__)"
   ```

2. Verificar configuración de pytest:
   ```bash
   poetry run pytest --collect-only
   ```

3. Ejecutar un test específico con verbose:
   ```bash
   poetry run pytest tests/test_example.py::test_function -v
   ```

4. Verificar conexión a base de datos:
   ```python
   # En un script de prueba
   import asyncio
   from database.setup import get_session_factory
   
   async def test_db_connection():
       try:
           session_factory = get_session_factory()
           async with session_factory() as session:
               result = await session.execute("SELECT 1")
               print("✅ Conexión a base de datos OK")
       except Exception as e:
           print(f"❌ Error de conexión: {e}")
   
   asyncio.run(test_db_connection())
   ```