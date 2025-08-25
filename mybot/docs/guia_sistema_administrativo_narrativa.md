# Guía del Sistema Administrativo de Narrativa

## Contenido
1. [Introducción al Sistema Administrativo de Narrativa](#introducción)
2. [Componentes Principales](#componentes-principales)
3. [Acceso y Navegación](#acceso-y-navegación)
4. [Gestión de Fragmentos](#gestión-de-fragmentos)
   - [Visualización de Fragmentos](#visualización-de-fragmentos)
   - [Creación de Fragmentos](#creación-de-fragmentos)
   - [Edición de Fragmentos](#edición-de-fragmentos)
   - [Eliminación de Fragmentos](#eliminación-de-fragmentos)
5. [Sistema de Conexiones](#sistema-de-conexiones)
   - [Conexiones entre Fragmentos](#conexiones-entre-fragmentos)
   - [Configuración de Opciones](#configuración-de-opciones)
6. [Lógica Condicional](#lógica-condicional)
   - [Requisitos de Pistas](#requisitos-de-pistas)
   - [Triggers y Efectos](#triggers-y-efectos)
7. [Herramientas de Análisis](#herramientas-de-análisis)
   - [Estadísticas Globales](#estadísticas-globales)
   - [Engagement por Fragmento](#engagement-por-fragmento)
8. [Visualización y Storyboard](#visualización-y-storyboard)
9. [Mejores Prácticas](#mejores-prácticas)
10. [Sistema de Pruebas](#sistema-de-pruebas)
    - [Cobertura de Pruebas](#cobertura-de-pruebas)
    - [Categorías de Prueba](#categorías-de-prueba)
    - [Evaluación de Preparación](#evaluación-de-preparación)

## Introducción

El Sistema Administrativo de Narrativa es una herramienta completa para la gestión de contenido narrativo interactivo dentro del bot "Diana". Permite a los administradores crear, editar y analizar fragmentos narrativos que forman la experiencia de storytelling para los usuarios.

Este sistema está diseñado para ofrecer:
- Gestión completa de fragmentos narrativos
- Visualización de estructura narrativa
- Análisis de engagement y estadísticas
- Configuración de condiciones y efectos
- Seguimiento del progreso de usuarios

## Componentes Principales

El sistema administrativo de narrativa consta de los siguientes componentes principales:

### 1. Fragmentos Narrativos

Los fragmentos son la unidad básica de contenido narrativo y pueden ser de tres tipos:

- **Fragmentos de Historia (STORY)**: Contienen texto narrativo principal de la historia.
- **Puntos de Decisión (DECISION)**: Permiten a los usuarios tomar decisiones que afectan el desarrollo de la narrativa.
- **Fragmentos Informativos (INFO)**: Proporcionan información adicional o contexto.

Cada fragmento contiene:
- Título y contenido principal
- Tipo de fragmento
- Conexiones a otros fragmentos (opciones)
- Requisitos para acceder (pistas necesarias)
- Triggers o efectos al completar el fragmento

### 2. Conexiones y Flujo Narrativo

Las conexiones definen cómo los fragmentos se relacionan entre sí, creando un flujo narrativo dinámico:

- **Conexiones de Salida**: Opciones que llevan desde un fragmento actual a otros fragmentos.
- **Conexiones de Entrada**: Fragmentos que pueden conducir al fragmento actual.

### 3. Sistema de Pistas

Las pistas (clues) son elementos que pueden ser desbloqueados y utilizados como requisitos:

- **Desbloqueo de Pistas**: Ocurre al completar ciertos fragmentos o tomar decisiones específicas.
- **Requisitos de Pistas**: Condiciones para acceder a ciertos fragmentos o opciones.

### 4. Triggers y Efectos

Los triggers definen efectos que se activan al interactuar con un fragmento:

- **Otorgar Puntos**: Recompensas para el sistema de gamificación.
- **Desbloquear Pistas**: Revela nueva información para el usuario.
- **Activar Eventos**: Puede iniciar otros eventos en el sistema.

## Acceso y Navegación

### Acceso al Panel Administrativo

El acceso al sistema administrativo de narrativa está restringido a usuarios con rol de administrador. Para acceder:

1. Acceda al menú de administración principal.
2. Seleccione la opción "Sistema Narrativo" o utilice el comando específico.

### Navegación Principal

El menú principal del sistema administrativo ofrece estas opciones:

- **📝 Fragmentos**: Gestión de fragmentos narrativos
- **🔖 Storyboard**: Visualización gráfica del flujo narrativo
- **📊 Analíticas**: Estadísticas y métricas de engagement
- **🔍 Buscar**: Búsqueda de fragmentos por título o contenido
- **➕ Nuevo Fragmento**: Creación rápida de nuevos fragmentos
- **🔄 Actualizar**: Actualiza las estadísticas del panel
- **🏠 Panel Admin**: Regresa al panel de administración principal

## Gestión de Fragmentos

### Visualización de Fragmentos

La lista de fragmentos muestra todos los fragmentos narrativos con opciones de filtrado y paginación:

- **Filtros por Tipo**: Permite filtrar por STORY, DECISION o INFO
- **Paginación**: Navegación entre páginas de resultados
- **Detalles**: Al seleccionar un fragmento se muestran sus detalles completos

#### Detalles del Fragmento

La vista detallada de un fragmento muestra:

- **Información Básica**: Título, tipo, estado, fechas
- **Contenido**: Texto completo del fragmento
- **Conexiones**: Opciones disponibles y destinos
- **Requisitos**: Pistas necesarias para acceder
- **Triggers**: Efectos activados al completar
- **Estadísticas**: Datos de engagement del fragmento

### Creación de Fragmentos

Para crear un nuevo fragmento narrativo:

1. Seleccione "➕ Nuevo Fragmento" en el menú principal
2. Seleccione el tipo de fragmento (STORY, DECISION, INFO)
3. Complete el formulario con:
   - **Título**: Nombre identificativo del fragmento
   - **Contenido**: Texto principal del fragmento
   - **Estado**: Activo o inactivo
4. Configure elementos avanzados (opcional):
   - **Conexiones**: Opciones y fragmentos destino
   - **Requisitos**: Pistas necesarias para acceder
   - **Triggers**: Efectos al completar el fragmento

### Edición de Fragmentos

Para editar un fragmento existente:

1. Localice el fragmento en la lista o mediante búsqueda
2. Seleccione el fragmento para ver sus detalles
3. Pulse "✏️ Editar" para modificar sus propiedades
4. Realice los cambios necesarios en cualquiera de sus componentes
5. Guarde los cambios

### Eliminación de Fragmentos

El sistema utiliza borrado lógico (no físico) de fragmentos:

1. Localice el fragmento en la lista o mediante búsqueda
2. Seleccione el fragmento para ver sus detalles
3. Pulse "❌ Eliminar" para marcar como inactivo
4. Confirme la acción cuando se solicite

## Sistema de Conexiones

### Conexiones entre Fragmentos

Las conexiones definen cómo se relacionan los fragmentos entre sí:

1. **Visualización de Conexiones**:
   - En la vista detallada de un fragmento, seleccione "🔄 Conexiones"
   - Verá tanto conexiones de entrada como de salida

2. **Conexiones de Salida**:
   - Opciones que llevan desde el fragmento actual a otros fragmentos
   - Incluyen texto de la opción y fragmento destino

3. **Conexiones de Entrada**:
   - Fragmentos que pueden conducir al fragmento actual
   - Muestra qué fragmentos tienen opciones que apuntan al fragmento actual

### Configuración de Opciones

Para fragmentos de tipo DECISION, es esencial configurar las opciones disponibles:

1. En el fragmento de decisión, seleccione "✏️ Editar Conexiones"
2. Para cada opción, defina:
   - **Texto**: Descripción de la opción que verá el usuario
   - **Fragmento Destino**: ID del fragmento al que lleva esta opción
   - **Requisitos**: Condiciones para que esta opción esté disponible (opcional)

## Lógica Condicional

### Requisitos de Pistas

Los requisitos determinan cuándo un fragmento está disponible para un usuario:

1. **Configuración de Requisitos**:
   - En la edición del fragmento, vaya a "Requisitos"
   - Añada los códigos de las pistas necesarias

2. **Comportamiento**:
   - El fragmento solo estará disponible si el usuario tiene todas las pistas requeridas
   - Se puede usar para crear ramas narrativas condicionadas

### Triggers y Efectos

Los triggers definen efectos que se activan al completar un fragmento:

1. **Tipos de Triggers**:
   - **points**: Otorga puntos al usuario
   - **clues**: Desbloquea nuevas pistas
   - **missions**: Avanza en misiones específicas
   - **achievements**: Progresa hacia logros

2. **Configuración de Triggers**:
   - En la edición del fragmento, vaya a "Triggers"
   - Defina el tipo y los parámetros específicos
   
   Ejemplo:
   ```json
   {
     "points": 10,
     "clues": ["CLAVE_SECRETA", "PISTA_IMPORTANTE"],
     "missions": {
       "mission_id": "increment_progress"
     }
   }
   ```

## Herramientas de Análisis

### Estadísticas Globales

El panel de estadísticas ofrece una visión general del sistema narrativo:

- **Total de Fragmentos**: Cantidad total de fragmentos en el sistema
- **Fragmentos Activos/Inactivos**: Estado de los fragmentos
- **Distribución por Tipo**: Cantidad de fragmentos por tipo
- **Usuarios en Narrativa**: Cantidad de usuarios participando
- **Tasa de Progresión**: Promedio de fragmentos completados por usuario

### Engagement por Fragmento

Para cada fragmento, se pueden analizar métricas específicas:

- **Usuarios Actuales**: Cuántos usuarios tienen este fragmento como actual
- **Visitas Totales**: Cuántos usuarios han pasado por este fragmento
- **Completados**: Cuántos usuarios han completado este fragmento
- **Tasa de Finalización**: Porcentaje de usuarios que completan el fragmento
- **Análisis de Opciones**: Para fragmentos de decisión, estadísticas de cada opción

## Visualización y Storyboard

El storyboard proporciona una visualización gráfica del flujo narrativo:

1. **Acceso al Storyboard**:
   - Seleccione "🔖 Storyboard" en el menú principal

2. **Funcionalidades**:
   - **Vista de Árbol**: Visualización jerárquica de fragmentos
   - **Conexiones**: Líneas que muestran relaciones entre fragmentos
   - **Filtros**: Opciones para simplificar la visualización
   - **Navegación**: Seleccione fragmentos para ver sus detalles

## Mejores Prácticas

Para aprovechar al máximo el sistema narrativo:

1. **Estructura Narrativa Clara**:
   - Planifique la estructura antes de crear fragmentos
   - Organice fragmentos en secuencias lógicas
   - Evite bucles infinitos o callejones sin salida

2. **Consistencia y Calidad**:
   - Mantenga un estilo consistente en todos los fragmentos
   - Revise el contenido para evitar errores
   - Utilice títulos descriptivos para facilitar la administración

3. **Uso Efectivo de Condiciones**:
   - Utilice requisitos para crear narrativas personalizadas
   - Emplee triggers para recompensar la progresión
   - Equilibre la complejidad de las condiciones

4. **Monitoreo y Optimización**:
   - Analice las estadísticas regularmente
   - Identifique fragmentos con baja tasa de finalización
   - Optimice basándose en el comportamiento real de los usuarios

5. **Documentación**:
   - Mantenga un registro de pistas y condiciones
   - Documente la estructura narrativa global
   - Use convenciones de nomenclatura consistentes

## Sistema de Pruebas

El sistema administrativo de narrativa está respaldado por una suite exhaustiva de pruebas que garantizan su integridad, rendimiento y manejo adecuado de errores.

### Configuración del Entorno de Pruebas

Para ejecutar las pruebas del sistema narrativo administrativo, se ha establecido un entorno especializado con las siguientes características:

1. **Scripts de Utilidad**:
   ```bash
   # Configuración del entorno
   ./setup.sh
   
   # Ejecución de pruebas
   ./test.sh
   
   # Pruebas específicas de narrativa
   ./run_narrative_admin_tests.py
   ```

2. **Configuración de pytest**:
   ```ini
   # pytest.ini
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

3. **Mocking Asíncrono**:
   ```python
   # Configuración correcta para mocks de SQLAlchemy async
   session_mock = AsyncMock()
   mock_context = AsyncMock()
   mock_context.__aenter__.return_value = session_mock
   session_mock.begin.return_value = mock_context
   
   # Mocks para aiogram 3
   callback = MagicMock()
   callback.answer = AsyncMock()
   ```

### Categorías de Prueba

1. **Pruebas de Integridad de Fragmentos**
   - Verificación de que las actualizaciones mantienen la integridad referencial
   - Prevención de referencias circulares y validación de fragmentos inactivos
   - Garantía de que el borrado lógico mantiene la integridad de la base de datos

2. **Pruebas de Integración con Event Bus**
   - Verificación de suscripción y publicación correcta de eventos
   - Degradación elegante ante fallos del Event Bus
   - Manejo adecuado de errores en handlers de eventos

3. **Pruebas de Integridad de Transacciones**
   - Validación de que las transacciones son atómicas
   - Verificación de restricciones para prevenir corrupción de datos
   - Validación de aislamiento de transacciones y manejo de errores

4. **Pruebas del Sistema de Pistas**
   - Validación de requisitos de pistas para acceso a fragmentos
   - Verificación de propagación de desbloqueo de pistas
   - Pruebas de pistas como requisitos para opciones específicas

5. **Pruebas de Rendimiento**
   - Validación de tiempos de respuesta para todas las operaciones
   - Optimización de consultas y transacciones

6. **Pruebas de Operaciones Concurrentes**
   - Verificación de manejo de operaciones administrativas simultáneas
   - Pruebas de actualizaciones concurrentes de conexiones
   - Validación de actualizaciones de estados narrativos de usuario

7. **Pruebas de Escenarios de Fallo**
   - Manejo de fallos de conexión a la base de datos
   - Validación de IDs inválidos y datos corruptos
   - Pruebas de condiciones de carrera y registro de errores

8. **Pruebas de Validación de Conexiones**
   - Verificación de validez de conexiones entre fragmentos
   - Validación de integridad del flujo narrativo
   - Pruebas de estructuras complejas con múltiples caminos

### Solución de Problemas Comunes

Si encuentra problemas al ejecutar las pruebas, consulte `TROUBLESHOOTING.md` para soluciones a problemas comunes, como:

1. **Error**: `'coroutine' object does not support the asynchronous context manager protocol`
   **Solución**: Configurar correctamente los mocks asíncronos para soportar context managers.

2. **Error**: `RuntimeWarning: coroutine was never awaited`
   **Solución**: Asegurarse de usar `await` con todas las coroutines y configurar los mocks correctamente.

3. **Error**: TypeErrors al comparar MagicMock con valores numéricos
   **Solución**: Configurar mocks con valores reales (no mocks) para atributos que se compararán.

### Ejecución de Pruebas

Para ejecutar las pruebas del sistema administrativo de narrativa:

```bash
# Ejecutar todas las pruebas
./run_narrative_admin_tests.py

# Modo verboso
./run_narrative_admin_tests.py -v

# Con cobertura
./run_narrative_admin_tests.py -c

# Un test específico
./run_narrative_admin_tests.py -t tests/integration/test_narrative_admin_integration.py::test_view_fragment_integration
```

### Mejores Prácticas para Pruebas

1. **Aislamiento**: Asegúrese de que cada prueba sea independiente.
2. **Fixtures Eficientes**: Use scopes adecuados para los fixtures.
3. **Mocking Adecuado**: Configure correctamente los AsyncMock para SQLAlchemy y aiogram.
4. **Limpieza**: Deje la base de datos limpia después de cada prueba.
5. **Validación Completa**: Verifique todos los aspectos de la funcionalidad probada.

Consulte la documentación completa en `README_SETUP.md` para más detalles sobre la configuración del entorno de pruebas.