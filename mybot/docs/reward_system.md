# Sistema Unificado de Recompensas y Desbloqueos

## Descripción General

El Sistema Unificado de Recompensas y Desbloqueos es un componente del bot que centraliza la gestión de todas las recompensas otorgadas a los usuarios. Este sistema proporciona una interfaz unificada para otorgar diferentes tipos de recompensas (puntos, pistas, logros) y mantiene un registro auditado de todas las recompensas otorgadas.

## Componentes Principales

### 1. Modelo de Datos: `RewardLog`

El modelo `RewardLog` en `database/transaction_models.py` registra todas las recompensas otorgadas a los usuarios:

```python
class RewardLog(Base):
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    reward_type = Column(String(50), nullable=False)  # 'points', 'clue', 'achievement'
    reward_data = Column(JSON, nullable=False)  # Datos específicos de la recompensa
    source = Column(String(100), nullable=True)  # Origen de la recompensa
    created_at = Column(DateTime, default=func.now(), nullable=False)
```

### 2. Modelo de Datos: `LorePiece` (Actualizado)

El modelo `LorePiece` en `database/models.py` ha sido actualizado para incluir campos adicionales:

```python
class LorePiece(Base):
    id = Column(Integer, primary_key=True, autoincrement=True)
    code_name = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    content_type = Column(String, nullable=False)  # Equivalente a clue_type en la especificación
    content = Column(Text, nullable=False)
    category = Column(String, nullable=True)
    is_main_story = Column(Boolean, default=False)
    unlock_condition_type = Column(String, nullable=True)
    unlock_condition_value = Column(String, nullable=True)
    related_fragments = Column(JSON, default=list, nullable=False)  # IDs de fragmentos relacionados
    unlock_conditions = Column(JSON, default=dict, nullable=False)  # Condiciones para desbloquear
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
```

### 3. Servicio: `RewardSystem`

El servicio `RewardSystem` en `services/reward_service.py` maneja toda la lógica de negocio relacionada con las recompensas:

#### Métodos Principales

- `grant_reward(user_id, reward_type, reward_data, source)`: Otorga recompensas de manera unificada
- `_grant_points_reward(user, reward_data, source)`: Otorga recompensa de puntos
- `_grant_clue_reward(user, reward_data, source)`: Otorga recompensa de pista
- `_grant_achievement_reward(user, reward_data, source)`: Otorga recompensa de logro

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
1. Utilizar el sistema para otorgar recompensas a los usuarios.
2. Monitorear las recompensas otorgadas a través de la tabla `reward_logs`.
3. Configurar triggers en los fragmentos narrativos para otorgar recompensas automáticas.

### Para Desarrolladores

#### Extender Funcionalidad

Para extender la funcionalidad del sistema:
1. Añadir nuevos tipos de recompensa al método `grant_reward`.
2. Implementar nuevos métodos privados para manejar los nuevos tipos de recompensa.
3. Actualizar el modelo `RewardLog` si es necesario almacenar información adicional.

#### Puntos de Integración

- `services/reward_service.py`: Lógica de negocio central
- `database/transaction_models.py`: Modelo de registro de recompensas
- `database/models.py`: Modelo de pistas (actualizado)
- `handlers/reward_test_handler.py`: Handlers de prueba

## Tests

Se han implementado tests unitarios en `tests/services/test_reward_service.py` que verifican:

1. Concesión de recompensas de puntos
2. Concesión de recompensas de pistas
3. Concesión de recompensas de logros

Para ejecutar los tests:

```bash
pytest tests/services/test_reward_service.py
```

## Validación de Funcionamiento

### Prueba Básica

1. Iniciar una conversación con el bot.
2. Enviar el comando `/test_reward_points`.
3. Verificar que se muestra un mensaje de confirmación.
4. Enviar el comando `/test_reward_clue`.
5. Verificar que se muestra un mensaje de confirmación.
6. Enviar el comando `/test_reward_achievement`.
7. Verificar que se muestra un mensaje de confirmación.

### Prueba de Integración

1. Otorgar una recompensa de puntos.
2. Verificar que se registra en la tabla `point_transactions`.
3. Otorgar una recompensa de pista.
4. Verificar que se registra en la tabla `user_lore_pieces`.
5. Otorgar una recompensa de logro.
6. Verificar que se añade al campo `achievements` del usuario.

### Prueba de Errores

1. Intentar otorgar una recompensa a un usuario que no existe.
2. Verificar que se muestra un mensaje de error apropiado.
3. Intentar otorgar una recompensa de pista con un código que no existe.
4. Verificar que se registra un warning en el log.

## Consideraciones de Seguridad

- Todos los accesos a la base de datos se realizan a través del middleware de sesión existente.
- Las operaciones se realizan dentro de transacciones para mantener la consistencia de los datos.
- Se implementa manejo de errores apropiado para prevenir estados inconsistentes.

## Mantenimiento

- El sistema está diseñado para ser extensible sin romper la compatibilidad con versiones anteriores.
- Los cambios en el modelo de datos deben realizarse con migraciones adecuadas.
- La documentación debe actualizarse junto con cualquier cambio en la funcionalidad.