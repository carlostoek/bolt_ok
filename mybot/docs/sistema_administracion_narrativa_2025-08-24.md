# Plan de Implementación del Sistema de Administración Narrativa
*Fecha: 2025-08-24*

## Resumen Ejecutivo

Este documento presenta un plan detallado para la implementación de un Sistema de Administración Narrativa para el bot Diana. El sistema permitirá a los administradores gestionar de manera eficiente el contenido narrativo, visualizar la estructura de la historia mediante storyboards, y analizar el engagement de los usuarios con la narrativa.

## Análisis del Sistema Existente

### Modelos de Datos
- El sistema utiliza `NarrativeFragment` y `UserNarrativeState` en `database/narrative_unified.py`
- Estructura de fragmentos con tipos (STORY, DECISION, INFO)
- Soporte para opciones, triggers y requisitos

### Flujo Narrativo Actual
- Manejo básico a través de `narrative_handlers.py` y `admin_narrative_handlers.py`
- Módulo `modules/narrative/story_engine.py` para la lógica de progresión
- Integración con `CoordinadorCentral` para flujos completos

### Integración con Admin
- Sistema de menús a través de `menu_manager` y `menu_factory`
- Estructura de teclados con patrones consistentes
- Routers admin en `handlers/admin/admin_menu.py`

## Componentes Planificados

### 1. NarrativeAdminService

```python
class NarrativeAdminService:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def get_all_fragments(self, page: int = 1, limit: int = 10, filter_type: str = None):
        """Obtiene fragmentos narrativos con paginación y filtrado opcional."""
        # Lógica para recuperar y paginar fragmentos
        
    async def get_fragment_details(self, fragment_id: str):
        """Obtiene detalles completos de un fragmento incluyendo estadísticas de uso."""
        # Lógica para obtener un fragmento específico con datos enriquecidos
        
    async def create_fragment(self, fragment_data: dict):
        """Crea un nuevo fragmento narrativo."""
        # Validación y creación de fragmento
        
    async def update_fragment(self, fragment_id: str, fragment_data: dict):
        """Actualiza un fragmento existente."""
        # Validación y actualización
        
    async def delete_fragment(self, fragment_id: str):
        """Marca un fragmento como inactivo (borrado lógico)."""
        # Nunca eliminar físicamente, solo marcar como inactivo
        
    async def get_fragment_connections(self, fragment_id: str):
        """Obtiene fragmentos conectados (entrada/salida) a un fragmento."""
        # Analizar triggers y choices para identificar conexiones
        
    async def update_fragment_connections(self, fragment_id: str, connections: list):
        """Actualiza las conexiones de un fragmento."""
        # Modificar choices para reflejar nuevas conexiones
        
    async def get_narrative_stats(self):
        """Obtiene estadísticas globales del sistema narrativo."""
        # Total de fragmentos, tipos, conexiones, usuarios activos, etc.
```

#### Integración con Módulos Existentes
- Reutilizar lógica de validación de `NarrativeLoader` si existe
- Coordinar con `CoordinadorCentral` para eventos de cambio
- Mantener compatibilidad con sistema de logs existente

### 2. Estructura de Teclados (narrative_admin_kb.py)

```python
def get_narrative_admin_keyboard():
    """Teclado principal de administración narrativa."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 Fragmentos", callback_data="narrative_fragments_list"),
                InlineKeyboardButton(text="🔖 Storyboard", callback_data="narrative_storyboard")
            ],
            [
                InlineKeyboardButton(text="📊 Analíticas", callback_data="narrative_analytics"),
                InlineKeyboardButton(text="🔍 Buscar", callback_data="narrative_search")
            ],
            [
                InlineKeyboardButton(text="➕ Nuevo Fragmento", callback_data="narrative_create_fragment")
            ],
            [
                InlineKeyboardButton(text="🔄 Actualizar", callback_data="narrative_admin_menu"),
                InlineKeyboardButton(text="🏠 Panel Admin", callback_data="admin_main_menu")
            ],
        ]
    )
    return keyboard

def get_narrative_fragments_list_keyboard(fragments, offset=0, limit=5, total=0, filter_type=None):
    """Teclado para la lista paginada de fragmentos."""
    # Implementación del teclado

def get_fragment_detail_keyboard(fragment_id):
    """Teclado para la vista detallada de un fragmento."""
    # Implementación del teclado

def get_storyboard_view_keyboard(root_id=None, view_type="tree"):
    """Teclado para la visualización del storyboard."""
    # Implementación del teclado

# Más teclados para diferentes funcionalidades...
```

### 3. Handlers (narrative_admin.py)

```python
# Router principal
router = Router()

# Estados FSM para creación/edición
class NarrativeFragmentStates(StatesGroup):
    selecting_type = State()
    entering_title = State()
    entering_content = State()
    configuring_choices = State()
    configuring_requirements = State()
    configuring_triggers = State()
    confirming_creation = State()
    
    # Más estados para edición, búsqueda, etc.

# Punto de entrada
@router.callback_query(F.data == "narrative_admin_menu")
async def show_narrative_admin(callback: CallbackQuery, session: AsyncSession):
    """Muestra el menú principal de administración narrativa."""
    # Verificar permisos de admin
    # Mostrar menú principal
    
# Listado de fragmentos
@router.callback_query(F.data == "list_fragments")
async def list_fragments(callback: CallbackQuery, session: AsyncSession):
    """Muestra la lista paginada de fragmentos."""
    # Obtener fragmentos paginados
    # Mostrar con teclado apropiado
    
# Handlers para creación (Form Flow)
@router.callback_query(F.data == "create_fragment")
async def start_fragment_creation(callback: CallbackQuery, state: FSMContext):
    """Inicia el flujo de creación de fragmento."""
    # Iniciar FSM y mostrar selección de tipo
    
# Handlers para visualización
@router.callback_query(F.data == "visualize_narrative")
async def visualize_narrative(callback: CallbackQuery, session: AsyncSession):
    """Muestra la visualización del storyboard."""
    # Iniciar StoryboardService
    # Generar y mostrar visualización

# Más handlers para diferentes funcionalidades...
```

### 4. StoryboardService

```python
class StoryboardService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.narrative_admin_service = NarrativeAdminService(session)
        
    async def generate_visualization_data(self, root_fragment_id=None, max_depth=3, view_type="tree"):
        """Genera datos para visualización del storyboard."""
        # Lógica para crear estructura de nodos y conexiones
        
    async def get_fragment_tree(self, fragment_id, direction="forward", depth=2):
        """Obtiene el árbol de fragmentos en una dirección."""
        # Lógica para navegar conexiones y construir árbol
        
    async def generate_node_representation(self, fragment):
        """Genera representación visual de un nodo de fragmento."""
        # Crear estructura de datos para representación
        
    async def get_connection_statistics(self, fragment_id):
        """Obtiene estadísticas de conexiones de un fragmento."""
        # Métricas como número de usuarios que siguen cada camino
        
    # Métodos auxiliares para diferentes tipos de visualizaciones...
```

## Plan de Integración

### Cambios en admin_menu.py

```python
# Importación del router
from .narrative_admin import router as narrative_admin_router

# Incluir router en la lista
router.include_router(narrative_admin_router)
```

### Modificación de Teclados Existentes

```python
def get_admin_manage_content_keyboard():
    """Returns the keyboard for content management options."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            # Líneas existentes...
            [
                InlineKeyboardButton(text="🎁 Catálogo VIP", callback_data="admin_content_rewards"),
                InlineKeyboardButton(text="📖 Narrativa", callback_data="narrative_admin_menu")  # Nueva opción
            ],
            # Más líneas existentes...
        ]
    )
    return keyboard
```

## Plan de Implementación por Fases

### Fase 1: Administración Básica
1. Crear `services/narrative_admin_service.py` con funciones básicas
2. Crear `keyboards/narrative_admin_kb.py` con teclados principales
3. Implementar `handlers/admin/narrative_admin.py` con handlers básicos
4. Integrar con `admin_menu.py`
5. Pruebas de funcionalidad básica

### Fase 2: Visualización y Edición Avanzada
1. Implementar `services/storyboard_service.py`
2. Extender `narrative_admin.py` con visualización
3. Agregar funcionalidad de edición avanzada
4. Pruebas de integración

### Fase 3: Analíticas y Optimizaciones
1. Implementar métricas de uso
2. Optimizar rendimiento de visualización
3. Agregar filtros y búsqueda avanzada
4. Pruebas de rendimiento

## Plan de Pruebas

### Estructura de Pruebas Unitarias

```python
# tests/services/test_narrative_admin_service.py
class TestNarrativeAdminService:
    @pytest.mark.asyncio
    async def test_get_all_fragments(self, session: AsyncSession):
        """Prueba la obtención paginada de fragmentos."""
        # Configurar datos de prueba
        service = NarrativeAdminService(session)
        
        # Crear fragmentos de prueba
        await self._create_test_fragments(session)
        
        # Probar funcionalidad
        result = await service.get_all_fragments(page=1, limit=10)
        
        # Verificar resultados
        assert "items" in result
        assert "total" in result
        assert len(result["items"]) > 0
        assert result["total"] > 0
```

### Pruebas de Integración

```python
# tests/integration/test_narrative_admin_integration.py
class TestNarrativeAdminIntegration:
    @pytest.mark.asyncio
    async def test_create_fragment_flow(self, session: AsyncSession):
        """Prueba el flujo completo de creación de fragmento."""
        # Mocks para callback, state y dependencias
        callback = AsyncMock()
        state = AsyncMock()
        
        # Simular flujo de creación...
```

### Pruebas de Rendimiento

```python
# tests/performance/test_narrative_admin_performance.py
class TestNarrativeAdminPerformance:
    @pytest.mark.asyncio
    async def test_large_fragments_list_performance(self, session: AsyncSession):
        """Prueba el rendimiento con una gran cantidad de fragmentos."""
        service = NarrativeAdminService(session)
        
        # Crear 100 fragmentos de prueba...
        
        # Medir tiempo de respuesta para diferentes tamaños de página...
```

## Consideraciones Técnicas

### Rendimiento
- Paginación para todas las listas
- Carga perezosa para visualizaciones
- Indexación adecuada en base de datos

### Seguridad
- Validación estricta de entradas para prevenir inyecciones
- Verificaciones de permisos en todos los handlers
- Logging detallado de acciones administrativas

### UX/UI
- Mensajes claros y confirmaciones para acciones destructivas
- Indicadores de progreso para operaciones largas
- Ayuda contextual para funciones complejas

## Beneficios del Sistema

1. **Gestión Eficiente**: Los administradores podrán crear, editar y gestionar el contenido narrativo de manera más eficiente y estructurada.

2. **Visualización Clara**: El storyboard proporcionará una visión clara de la estructura narrativa, facilitando la comprensión de las conexiones entre fragmentos.

3. **Análisis de Engagement**: Las métricas de uso permitirán identificar qué partes de la narrativa generan mayor engagement.

4. **Calidad Mejorada**: La visualización y edición avanzada contribuirán a una mayor coherencia y calidad del contenido narrativo.

5. **Experiencia de Usuario Optimizada**: Un contenido narrativo mejor gestionado resultará en una experiencia de usuario más satisfactoria.

## Conclusión

El Sistema de Administración Narrativa propuesto proporcionará herramientas robustas para la gestión de contenido narrativo, visualización de storyboards y análisis de engagement. Su implementación en fases permitirá una integración gradual y sin disrupciones con el sistema existente, mejorando significativamente la capacidad de administración del bot Diana.