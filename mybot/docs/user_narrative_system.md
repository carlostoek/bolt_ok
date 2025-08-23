# Sistema de Progresión de Usuario Unificado

## Descripción General

El Sistema de Progresión de Usuario Unificado es un componente del bot que permite rastrear y gestionar el progreso de los usuarios en la experiencia narrativa. Este sistema mantiene un registro detallado de los fragmentos visitados, completados y las pistas desbloqueadas por cada usuario.

## Componentes Principales

### 1. Modelo de Datos: `UserNarrativeState`

El modelo `UserNarrativeState` en `database/narrative_unified.py` representa el estado narrativo de un usuario:

```python
class UserNarrativeState(Base):
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    current_fragment_id = Column(String, ForeignKey('narrative_fragments_unified.id'), nullable=True)
    visited_fragments = Column(JSON, default=list, nullable=False)  # Lista de IDs de fragmentos visitados
    completed_fragments = Column(JSON, default=list, nullable=False)  # Lista de IDs de fragmentos completados
    unlocked_clues = Column(JSON, default=list, nullable=False)  # Lista de códigos de pistas desbloqueadas
```

#### Métodos del Modelo

- `get_progress_percentage(session)`: Calcula el porcentaje de progreso del usuario basado en el número de fragmentos completados en relación con el total de fragmentos activos.
- `has_unlocked_clue(clue_code)`: Verifica si el usuario ha desbloqueado una pista específica.

### 2. Servicio: `UserNarrativeService`

El servicio `UserNarrativeService` en `services/user_narrative_service.py` maneja toda la lógica de negocio relacionada con la progresión del usuario:

#### Métodos Principales

- `get_or_create_user_state(user_id)`: Obtiene o crea el estado narrativo de un usuario.
- `update_current_fragment(user_id, fragment_id)`: Actualiza el fragmento actual del usuario.
- `mark_fragment_completed(user_id, fragment_id)`: Marca un fragmento como completado por el usuario.
- `unlock_clue(user_id, clue_code)`: Desbloquea una pista para el usuario.
- `check_user_access(user_id, fragment_id)`: Verifica si un usuario tiene acceso a un fragmento.
- `get_user_progress_percentage(user_id)`: Obtiene el porcentaje de progreso del usuario.
- `reset_user_progress(user_id)`: Restablece el progreso narrativo del usuario.

### 3. Handlers

Los handlers en `handlers/user_narrative_handler.py` proporcionan una interfaz para que los usuarios interactúen con el sistema:

- `/start_narrative`: Inicia la experiencia narrativa para el usuario.
- `/narrative_progress`: Muestra el progreso del usuario en la narrativa.
- `/unlock_clue`: Permite al usuario desbloquear una pista manualmente.

## Integración con Otros Sistemas

### Base de Datos

El sistema utiliza los siguientes modelos existentes:
- `User` (de `database/models.py`)
- `NarrativeFragment` (de `database/narrative_unified.py`)
- `LorePiece` (de `database/models.py`)

### Sistema de Puntos

Cuando un usuario completa un fragmento, los triggers del fragmento pueden otorgar puntos al usuario a través del sistema de puntos existente.

### Sistema de Pistas

El sistema interactúa con el sistema de pistas (`LorePiece`) para verificar y desbloquear pistas para los usuarios.

## Implementación e Integración

### Requisitos

- Python 3.8+
- Aiogram 3.x
- SQLAlchemy async
- Base de datos compatible con SQLAlchemy

### Instalación

El sistema se integra automáticamente con el bot existente. No se requieren pasos adicionales de instalación más allá de los ya implementados en el bot.

### Configuración

No se requiere configuración adicional. El sistema utiliza las mismas configuraciones de base de datos que el bot principal.

## Uso

### Para Administradores

Los administradores pueden:
1. Crear y gestionar fragmentos narrativos usando los comandos existentes.
2. Monitorear el progreso de los usuarios a través de la base de datos.
3. Configurar triggers en los fragmentos para otorgar recompensas automáticas.

### Para Desarrolladores

#### Extender Funcionalidad

Para extender la funcionalidad del sistema:
1. Añadir nuevos campos al modelo `UserNarrativeState` si es necesario.
2. Implementar nuevos métodos en `UserNarrativeService`.
3. Crear nuevos handlers si se requiere una interfaz de usuario adicional.

#### Puntos de Integración

- `services/user_narrative_service.py`: Lógica de negocio central
- `database/narrative_unified.py`: Modelo de datos
- `handlers/user_narrative_handler.py`: Interfaz de usuario

## Tests

Se han implementado tests unitarios en `tests/services/test_user_narrative_service.py` que verifican:

1. Creación de nuevos estados de usuario
2. Actualización del fragmento actual
3. Desbloqueo de pistas
4. Verificación de acceso del usuario
5. Cálculo del progreso

Para ejecutar los tests:

```bash
pytest tests/services/test_user_narrative_service.py
```

## Validación de Funcionamiento

### Prueba Básica

1. Iniciar una conversación con el bot.
2. Enviar el comando `/start_narrative`.
3. Verificar que se muestra el primer fragmento de historia.
4. Enviar el comando `/narrative_progress`.
5. Verificar que se muestra el porcentaje de progreso (0% si es la primera vez).

### Prueba de Integración

1. Completar un fragmento que tenga triggers de recompensa.
2. Verificar que se otorgan los puntos correspondientes.
3. Verificar que se desbloquean las pistas especificadas en los triggers.

### Prueba de Errores

1. Intentar desbloquear una pista que no existe.
2. Verificar que se muestra un mensaje de error apropiado.
3. Intentar acceder a un fragmento que no existe.
4. Verificar que se niega el acceso correctamente.

## Consideraciones de Seguridad

- Todos los accesos a la base de datos se realizan a través del middleware de sesión existente.
- Las operaciones se realizan dentro de transacciones para mantener la consistencia de los datos.
- Se implementa manejo de errores apropiado para prevenir estados inconsistentes.

## Mantenimiento

- El sistema está diseñado para ser extensible sin romper la compatibilidad con versiones anteriores.
- Los cambios en el modelo de datos deben realizarse con migraciones adecuadas.
- La documentación debe actualizarse junto con cualquier cambio en la funcionalidad.