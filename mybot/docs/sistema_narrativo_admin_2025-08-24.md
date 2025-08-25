# Diseño del Sistema de Administración Narrativa
*Fecha: 2025-08-24*

## Resumen Ejecutivo

Se propone la implementación de un sistema de administración narrativa integral para el bot Diana que permitirá:
- Gestión robusta de contenido narrativo
- Creación visual de storyboards
- Administración de escenas
- Interfaz administrativa especializada integrada con la arquitectura existente

## Arquitectura Actual

El sistema narrativo utiliza una estructura modular con:
1. `UnifiedNarrativeService` - Servicio principal que gestiona la progresión narrativa
2. `NarrativeFragmentService` - Maneja operaciones individuales de fragmentos
3. Modelo `NarrativeFragment` - Representa piezas de contenido con opciones y triggers
4. Funcionalidad administrativa básica para interacción con usuarios pero carece de gestión de contenido avanzada

## Diseño Propuesto

### 1. Módulo de Administración Narrativa

```
Sistema de Administración Narrativa
├── Editor de Storyboard
│   ├── Relaciones visuales entre fragmentos
│   ├── Conexiones de escenas con drag-and-drop
│   └── Visualización del flujo de la historia
├── Gestor de Contenido
│   ├── Editor de fragmentos con texto enriquecido
│   ├── Soporte para adjuntar medios
│   └── Historial de versiones
└── Analíticas Narrativas
    ├── Seguimiento de progresión de usuarios
    ├── Análisis de puntos de decisión
    └── Métricas de engagement
```

## Plan de Implementación

### Fase 1: Administración Narrativa Básica
- `/handlers/admin/narrative_admin.py`: Nuevo archivo con interfaz administrativa
- `/services/narrative_admin_service.py`: Capa de servicio para operaciones administrativas
- `/handlers/admin/admin_menu.py:34`: Añadir importación del router de admin narrativo
- `/handlers/admin/admin_menu.py:45`: Incluir router de admin narrativo

### Fase 2: Visualización de Storyboard
- `/services/storyboard_service.py`: Servicio para representación visual
- `/keyboards/narrative_admin_kb.py`: Teclados especializados para administración

### Fase 3: Analíticas y Pruebas
- `/services/narrative_analytics_service.py`: Métricas de uso e insights
- `/tests/services/test_narrative_admin.py`: Cobertura de pruebas para funciones administrativas

## Mitigación de Riesgos
- **Integridad de Datos**: Implementar historial de versiones y validación antes de guardar fragmentos
- **Impacto en Experiencia de Usuario**: Agregar estados borrador/publicado para prevenir exposición de contenido incompleto
- **Rendimiento**: Paginación y carga perezosa para visualización de storyboard con muchos fragmentos
- **Migración**: Proporcionar capa de compatibilidad hacia atrás para contenido narrativo existente

## Pruebas Requeridas
- `test_narrative_admin_service.py`: Probar edición de fragmentos, validación, relaciones
- `test_storyboard_service.py`: Probar generación de visualización y conexiones de fragmentos
- `test_narrative_admin_integration.py`: Integración con funcionalidad narrativa existente

## Detalles de Implementación

### 1. Servicio de Administración Narrativa
```python
class NarrativeAdminService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.fragment_service = NarrativeFragmentService(session)
    
    async def create_fragment_with_connections(self, fragment_data, connections):
        # Crear fragmento con relaciones adecuadas
        
    async def get_connected_fragments(self, fragment_id):
        # Devolver fragmentos conectados a este
        
    async def update_fragment_and_connections(self, fragment_id, fragment_data, connections):
        # Actualizar tanto el contenido del fragmento como las conexiones
        
    async def generate_storyboard_view(self, root_fragment_id=None):
        # Generar datos de visualización para el storyboard
```

### 2. Manejadores de Interfaz Administrativa
```python
@router.callback_query(F.data == "narrative_admin_menu")
async def show_narrative_admin(callback: CallbackQuery, session: AsyncSession):
    """Interfaz principal de administración narrativa."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    keyboard = get_narrative_admin_keyboard()
    await menu_manager.update_menu(
        callback,
        "🔖 **Administración de Narrativa**\n\n"
        "Gestiona el contenido narrativo, crea y edita fragmentos, "
        "visualiza conexiones y analiza la progresión de los usuarios.",
        keyboard,
        session,
        "narrative_admin_main"
    )
```

### 3. Visualización de Storyboard
```python
class StoryboardService:
    async def generate_graph_data(self, session, root_fragment_id=None):
        """Genera estructura de datos de grafo para visualización."""
        # Generar nodos y bordes para fragmentos y sus conexiones
        
    async def get_fragment_statistics(self, session, fragment_id):
        """Obtiene estadísticas de uso para un fragmento específico."""
        # Calcular métricas de engagement, finalización y selección de ramas
```

## Conclusión

La implementación de este diseño proporcionará al sistema narrativo capacidades de administración robustas, herramientas visuales de storyboard y gestión de contenido mejorada - abordando las limitaciones actuales mientras se integra con la arquitectura existente.

Este sistema permitirá a los administradores:
- Crear y visualizar historias complejas con ramificaciones
- Editar contenido narrativo con herramientas avanzadas
- Analizar el rendimiento y engagement de diferentes fragmentos narrativos
- Gestionar el flujo de la narrativa de manera visual e intuitiva