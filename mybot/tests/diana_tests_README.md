# Pruebas del Sistema Emocional Diana

Este directorio contiene un conjunto completo de pruebas para validar la integración y funcionamiento del sistema emocional Diana con los sistemas existentes del bot.

## Estructura de las Pruebas

Las pruebas están organizadas en las siguientes categorías:

### Pruebas Unitarias (directorio `unit/diana/`)

- **test_diana_emotional_service.py**: Pruebas unitarias para el servicio `DianaEmotionalService`, comprobando cada método individualmente.
- **test_diana_handlers.py**: Pruebas para los handlers de Diana, asegurando que responden correctamente a los comandos y mensajes.
- **test_diana_personalization.py**: Pruebas específicas para la personalización de mensajes basada en el estado emocional.
- **test_diana_contradictions.py**: Pruebas para el sistema de detección y resolución de contradicciones.

### Pruebas de Integración (directorio `integration/diana/`)

- **test_diana_integration.py**: Pruebas de integración para verificar la interacción entre Diana y el coordinador central.
- **test_diana_persistence.py**: Pruebas para verificar la persistencia correcta del estado emocional entre sesiones.
- **test_diana_load.py**: Pruebas de carga/estrés para verificar el rendimiento bajo condiciones de uso intensivo.
- **test_diana_non_interference.py**: Pruebas para asegurar que Diana no interfiere con la funcionalidad base del bot.

## Ejecución de las Pruebas

Se proporciona un script `run_diana_tests.py` para facilitar la ejecución de todas las pruebas o de categorías específicas.

### Ejecutar todas las pruebas:

```bash
python tests/run_diana_tests.py
```

### Ejecutar pruebas por categoría:

```bash
# Solo pruebas unitarias
python tests/run_diana_tests.py --category unit

# Solo pruebas de integración
python tests/run_diana_tests.py --category integration

# Categorías específicas
python tests/run_diana_tests.py --category servicio
python tests/run_diana_tests.py --category handlers
python tests/run_diana_tests.py --category personalizacion
python tests/run_diana_tests.py --category contradicciones
python tests/run_diana_tests.py --category integracion
python tests/run_diana_tests.py --category persistencia
python tests/run_diana_tests.py --category carga
python tests/run_diana_tests.py --category no_interferencia
```

### Modo verboso:

```bash
python tests/run_diana_tests.py --verbose
# o
python tests/run_diana_tests.py -v
```

### Generar informe de cobertura:

```bash
python tests/run_diana_tests.py --coverage
```

## Recomendaciones para las Pruebas

1. **Ejecutar pruebas frecuentemente**: Las pruebas unitarias y de integración básicas deben ejecutarse frecuentemente durante el desarrollo.

2. **Pruebas de carga**: Las pruebas de carga son más intensivas en recursos y pueden tardar más tiempo. Ejecútalas antes de desplegar cambios importantes.

3. **Cobertura de código**: Usa la opción `--coverage` periódicamente para asegurarte de que todas las funcionalidades clave están siendo probadas.

4. **Verificación de no interferencia**: Las pruebas de no interferencia son especialmente importantes para asegurar que Diana puede ser desplegada sin afectar a la funcionalidad existente.

## Resolución de Problemas

Si encuentras problemas al ejecutar las pruebas:

1. **Dependencias**: Asegúrate de tener todas las dependencias instaladas:
   ```bash
   pip install pytest pytest-asyncio pytest-cov
   ```

2. **Base de datos**: Las pruebas utilizan mocks para la base de datos, pero algunos tests pueden requerir una configuración específica de entorno.

3. **Aislamiento**: Si una categoría específica de pruebas falla, ejecuta solo esa categoría en modo verboso para obtener más detalles:
   ```bash
   python tests/run_diana_tests.py --category <categoria_fallida> --verbose
   ```

4. **Ejecución individual**: Para ejecutar una prueba específica:
   ```bash
   python -m pytest tests/unit/diana/test_diana_emotional_service.py::test_store_emotional_memory_success -v
   ```