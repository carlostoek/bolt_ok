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

### Sistema de Menús Diana
- Sistema de menús completo y avanzado implementado en `services/diana_menu_system.py`
- Cuatro módulos de menús especializados:
  - `DianaAdminMenu`: Menú administrativo con más de 30 botones
  - `DianaUserMenu`: Menú para usuarios regulares
  - `DianaNarrativeMenu`: Menú de narrativa
  - `DianaGamificationMenu`: Menú de gamificación
- Integración a través de `services/diana_menu_integration_impl.py`
- Soporte para navegación, callbacks y compatibilidad con el sistema existente

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
```

## Plan de Integración con Diana Menu System

### Integración con DianaAdminMenu

El sistema actual ya cuenta con una sección narrativa en `services/diana_menus/admin_menu.py` que incluye:

```python
async def show_narrative_admin(self, callback: CallbackQuery) -> None:
    """
    Narrative content administration panel.
    """
    if not await is_admin(callback.from_user.id, self.session):
        await callback.answer("❌ Acceso denegado", show_alert=True)
        return
    
    try:
        # Get narrative statistics
        narrative_stats = await self._get_narrative_stats()
        
        text = f"""
📖 **ADMINISTRACIÓN NARRATIVA**
*Control del contenido y experiencias interactivas*

━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 **Estado del Contenido**
• Fragmentos totales: {narrative_stats.get('total_fragments', 0)}
• Fragmentos VIP: {narrative_stats.get('vip_fragments', 0)}
• Usuarios en historia: {narrative_stats.get('users_in_story', 0)}
• Decisiones disponibles: {narrative_stats.get('total_decisions', 0)}

🎭 **Personajes**
• Diana - Fragmentos: {narrative_stats.get('diana_fragments', 0)}
• Lucien - Fragmentos: {narrative_stats.get('lucien_fragments', 0)}
• Interacciones activas: {narrative_stats.get('active_interactions', 0)}

🔓 **Contenido VIP**
• Accesos VIP hoy: {narrative_stats.get('vip_access_today', 0)}
• Fragmentos premium: {narrative_stats.get('premium_content', 0)}
• Conversiones a VIP: {narrative_stats.get('vip_conversions', 0)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━

✍️ **Herramientas de Creación**
Gestiona la experiencia narrativa completa
        """
        
        keyboard = [
            [
                InlineKeyboardButton("📝 Gestionar Fragmentos", callback_data="admin_fragments_manage"),
                InlineKeyboardButton("🔮 Decisiones", callback_data="admin_decisions_manage")
            ],
            [
                InlineKeyboardButton("🎭 Personajes", callback_data="admin_characters_manage"),
                InlineKeyboardButton("👑 Contenido VIP", callback_data="admin_vip_content")
            ],
            [
                InlineKeyboardButton("🗝️ Pistas", callback_data="admin_hints_manage"),
                InlineKeyboardButton("📊 Progreso Usuarios", callback_data="admin_narrative_progress")
            ],
            [
                InlineKeyboardButton("🎨 Personalización", callback_data="admin_narrative_themes"),
                InlineKeyboardButton("⚙️ Configuración", callback_data="admin_narrative_config")
            ],
            [
                InlineKeyboardButton("◀️ Volver", callback_data="admin_menu"),
                InlineKeyboardButton("❌ Cerrar", callback_data="close_menu")
            ]
        ]
        
        await safe_edit(
            callback.message,
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        await callback.answer("📖 Administración narrativa cargada")
        
    except Exception as e:
        logger.error(f"Error showing narrative admin: {e}")
        await callback.answer("❌ Error cargando administración narrativa", show_alert=True)
```

Nuestra implementación deberá:
1. Implementar los handlers para las callback `admin_fragments_manage`
2. Integrarse con el sistema de menús existente
3. Compartir estadísticas con el DianaAdminMenu

## Plan de Implementación por Fases

### Fase 1: Administración Básica
1. Crear `services/narrative_admin_service.py` con funciones básicas
2. Crear `handlers/admin/narrative_admin.py` con handlers básicos
3. Integrar con DianaAdminMenu existente
4. Implementar handlers para callback_data "admin_fragments_manage"
5. Pruebas de funcionalidad básica

### Fase 2: Visualización y Edición Avanzada
1. Implementar `services/storyboard_service.py`
2. Extender handlers con visualización
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

### Pruebas de Integración con Diana Menu System

```python
# tests/integration/test_diana_narrative_integration.py
class TestDianaNarrativeIntegration:
    @pytest.mark.asyncio
    async def test_admin_fragments_manage(self, session: AsyncSession):
        """Prueba la integración con el botón admin_fragments_manage del Diana Menu System."""
        # Configurar callback
        callback = AsyncMock()
        callback.data = "admin_fragments_manage"
        
        # Simular handler
        from handlers.admin.narrative_admin import handle_admin_fragments_manage
        await handle_admin_fragments_manage(callback, session)
        
        # Verificar que se actualiza el mensaje correctamente
        assert callback.message.edit_text.called or safe_edit.called
```

## Consideraciones Técnicas

### Integración con Diana Menu System
- Mantener compatibilidad con el sistema de menús existente
- Implementar handlers para todos los callback_data definidos en DianaAdminMenu
- Compartir estadísticas para mostrar en el panel administrativo
- Respetar la estética y estructura de los menús existentes

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

El Sistema de Administración Narrativa propuesto proporcionará herramientas robustas para la gestión de contenido narrativo, visualización de storyboards y análisis de engagement. Su implementación se integrará perfectamente con el sistema de menús Diana existente, manteniendo la coherencia y usabilidad del sistema actual mientras añade funcionalidades avanzadas de gestión narrativa.