# Sistema de Fragmentos Narrativos Unificados

## Descripción

El sistema de Fragmentos Narrativos Unificados permite crear y gestionar diferentes tipos de contenido narrativo en una sola estructura. Los fragmentos pueden ser de tres tipos:

1. **STORY**: Fragmentos de historia principal
2. **DECISION**: Puntos de decisión con opciones
3. **INFO**: Fragmentos informativos

## Características

- **Tipos de fragmentos**: Soporte para historia, decisiones e información
- **Opciones de decisión**: Para fragmentos de tipo DECISION
- **Triggers**: Efectos y recompensas que se activan al interactuar con el fragmento
- **Requisitos de pistas**: Pistas necesarias para acceder al fragmento
- **Gestión completa**: Crear, leer, actualizar y eliminar fragmentos

## Comandos de Administrador

### `/create_fragment`
Inicia el proceso de creación de un nuevo fragmento narrativo. Se solicitará:
1. Título del fragmento
2. Contenido del fragmento
3. Tipo de fragmento (Historia, Decisión, Información)
4. Opciones (solo para fragmentos de decisión)
5. Triggers (recompensas/efectos)
6. Pistas requeridas

### `/list_fragments`
Muestra una lista de todos los fragmentos narrativos agrupados por tipo.

### `/get_fragment`
Permite obtener los detalles de un fragmento específico proporcionando su ID.

## Estructura del Modelo

```python
class NarrativeFragment(Base):
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    fragment_type = Column(String(20), nullable=False)  # STORY, DECISION, INFO
    choices = Column(JSON, default=list, nullable=False)  # Para puntos de decisión
    triggers = Column(JSON, default=dict, nullable=False)  # Disparadores de recompensas/pistas
    required_clues = Column(JSON, default=list, nullable=False)  # Pistas requeridas
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
```

## Ejemplos de Uso

### Crear un fragmento de historia
```
Título: Introducción al Misterio
Contenido: En una noche oscura, un misterio inquietante esperaba ser resuelto.
Tipo: Historia
Opciones: ninguna
Triggers: ninguno
Pistas requeridas: ninguna
```

### Crear un fragmento de decisión
```
Título: Cruce en el Bosque
Contenido: Llegas a un cruce en el bosque. ¿Qué camino tomas?
Tipo: Decisión
Opciones: [{"text": "Camino de la izquierda", "next_fragment_id": "fragment-2"}, {"text": "Camino de la derecha", "next_fragment_id": "fragment-3"}]
Triggers: {"reward_points": 5}
Pistas requeridas: pista-bosque
```

### Crear un fragmento informativo
```
Título: Historia del Castillo
Contenido: El castillo fue construido en el siglo XV por el rey Alonso.
Tipo: Información
Opciones: ninguna
Triggers: {"unlock_lore": "historia-castillo"}
Pistas requeridas: ninguna
```

## Servicio de Gestión

El `NarrativeFragmentService` proporciona métodos para:
- Crear fragmentos
- Obtener fragmentos por ID
- Obtener fragmentos por tipo
- Actualizar fragmentos
- Eliminar fragmentos (soft delete)
- Verificar acceso de usuario basado en pistas

## Consideraciones Técnicas

- Los fragmentos se identifican con UUIDs para garantizar unicidad global
- Los triggers y opciones se almacenan en formato JSON para flexibilidad
- El sistema utiliza soft delete (is_active) para mantener la integridad de datos
- Se implementan índices para optimizar las búsquedas por tipo y estado