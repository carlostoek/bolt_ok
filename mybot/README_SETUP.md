# Configuración del Entorno de Desarrollo

## Requisitos Previos

- Python 3.8 o superior
- Poetry (manejador de dependencias)
- Git

## Configuración Inicial

1. **Clonar el repositorio:**
   ```bash
   git clone <url-del-repositorio>
   cd mybot
   ```

2. **Ejecutar el script de setup:**
   ```bash
   ./setup.sh
   ```

   Este script:
   - Verifica e instala Poetry si no está presente
   - Instala todas las dependencias del proyecto
   - Configura la base de datos
   - Verifica que los tests puedan ejecutarse

## Estructura del Proyecto

```
mybot/
├── bot.py              # Punto de entrada principal
├── database/           # Modelos y configuración de base de datos
├── handlers/           # Manejadores de eventos de Telegram
├── services/           # Lógica de negocio
├── tests/              # Tests unitarios e integración
├── setup.sh            # Script de configuración
├── test.sh             # Script para ejecutar tests
└── dev.sh              # Script para desarrollo local
```

## Comandos Disponibles

### Configuración
```bash
./setup.sh              # Configuración inicial del entorno
```

### Desarrollo
```bash
./dev.sh                # Iniciar bot en modo desarrollo
./dev.sh debug          # Iniciar bot en modo debug
./dev.sh test           # Iniciar watcher de tests
```

### Testing
```bash
./test.sh               # Ejecutar todos los tests
./test.sh quick         # Ejecutar tests rápidos
./test.sh unit          # Ejecutar solo tests unitarios
./test.sh integration   # Ejecutar solo tests de integración
./test.sh coverage      # Ejecutar tests con cobertura
```

## Solución de Problemas

### Problemas Comunes

1. **Poetry no encontrado:**
   ```bash
   pip install poetry
   ```

2. **Dependencias no instaladas:**
   ```bash
   poetry install
   ```

3. **Tests fallando por configuración:**
   ```bash
   ./setup.sh
   ```

4. **Problemas con tests asíncronos:**
   Consulta `TROUBLESHOOTING.md` para soluciones detalladas a problemas específicos con:
   - Configuración de pytest-asyncio
   - Problemas de coroutines no esperadas (never awaited)
   - Errores de async context manager
   - Problemas de mocking en código asíncrono

### Verificación del Entorno

Para verificar que todo está correctamente configurado:

```bash
poetry run pytest --version
poetry run python -c "import aiogram; print('Aiogram OK')"
poetry run python -c "import sqlalchemy; print('SQLAlchemy OK')"
poetry run python -c "import pytest_asyncio; print('pytest-asyncio OK')"
```

### Configuración de Testing Asíncrono

El proyecto utiliza pytest-asyncio para tests asíncronos. La configuración se encuentra en `pytest.ini`:

```ini
[tool:pytest]
asyncio_mode = auto
python_files = test_*.py
python_classes = Test*
python_functions = test_*
testpaths = tests
addopts = --cov=. --cov-report=term-missing
asynciodebug = true
log_cli = true
log_cli_level = INFO
```

Notas importantes:

1. **Modo asyncio**: Configurado como "auto" para detectar automáticamente tests asíncronos
2. **Fixtures asíncronas**: Usar siempre el decorador `@pytest_asyncio.fixture`
3. **Tests asíncronos**: Usar el decorador `@pytest.mark.asyncio`
4. **Mocking asíncrono**: Configurar correctamente AsyncMock para context managers

## Mejores Prácticas

1. **Activar el entorno virtual de Poetry:**
   ```bash
   poetry shell
   ```

2. **Agregar nuevas dependencias:**
   ```bash
   poetry add nombre-del-paquete        # Dependencia de producción
   poetry add --group dev nombre-del-paquete  # Dependencia de desarrollo
   ```

3. **Ejecutar comandos dentro del entorno Poetry:**
   ```bash
   poetry run python script.py
   poetry run pytest
   ```

## Configuración de IDE

### VS Code

Recomendado instalar las extensiones:
- Python
- Pylance
- pytest

Configuración recomendada en `settings.json`:
```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.pytestArgs": [
        "tests"
    ]
}
```

## Variables de Entorno

Crear un archivo `.env` en la raíz del proyecto:
```env
BOT_TOKEN=tu_token_de_telegram
DATABASE_URL=sqlite+aiosqlite:///telegram_bot.db
VIP_CHANNEL_ID=-1001234567890
```