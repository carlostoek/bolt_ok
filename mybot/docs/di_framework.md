# Framework de Inyección de Dependencias

## Visión General

Este documento describe la implementación del framework de inyección de dependencias (DI) para los servicios del bot Diana. El framework mejora la arquitectura del sistema proporcionando:

- **Alta cohesión y bajo acoplamiento** entre servicios
- **Testabilidad mejorada** mediante interfaces y mocks
- **Resolución de dependencias circulares** 
- **Arquitectura mantenible y escalable**

## Componentes Principales

### 1. Interfaces de Servicios

Las interfaces definen contratos claros para cada servicio:

- `IUserNarrativeService`: Gestión del estado narrativo del usuario
- `IRewardSystem`: Sistema centralizado de recompensas 
- `INotificationService`: Servicio de notificaciones con prioridades
- `IPointService`: Gestión de la economía de puntos

Ubicación: `/services/interfaces/`

### 2. Contenedor de Dependencias

El contenedor gestiona el ciclo de vida y la resolución de dependencias de los servicios:

- Basado en el patrón Service Container
- Proporciona gestión de instancias singleton y transient
- Configurado para resolver automáticamente las dependencias
- Soporte para inyección de AsyncSession y Bot

Ubicación: `/services/container.py`

### 3. Utilidades de Integración

Componentes para integrar el DI en el flujo de la aplicación:

- `DIContainerMiddleware`: Middleware para inyectar el contenedor en handlers
- `DISetup`: Clase singleton para inicializar y acceder al contenedor

Ubicación: 
- `/services/di_middleware.py`
- `/services/di_setup.py`

## Patrón de Inyección

### Constructor Injection

Los servicios reciben sus dependencias a través del constructor:

```python
def __init__(self, session: AsyncSession, reward_system: IRewardSystem):
    self.session = session
    self.reward_system = reward_system
```

### Resolución de Dependencias Circulares

Se implementan estas estrategias para resolver dependencias circulares:

1. **Inyección Opcional**: Dependencias opcionales con valores por defecto
   ```python
   def __init__(self, session: AsyncSession, notification_service: Optional[INotificationService] = None):
   ```

2. **Verificación de Nulos**: Comprobaciones antes de usar dependencias opcionales
   ```python
   if self.notification_service:
       await self.notification_service.add_notification(...)
   ```

## Integración en Handlers

Los handlers pueden acceder a los servicios a través del contenedor:

```python
async def handler(message: Message, container: Container = None):
    narrative_service = container.get_user_narrative_service()
    await narrative_service.update_current_fragment(user_id, fragment_id)
```

## Pruebas

El framework facilita las pruebas unitarias mediante la inyección de mocks:

```python
@pytest.fixture
def user_narrative_service(mock_session, mock_reward_system):
    return UserNarrativeService(
        session=mock_session, 
        reward_system=mock_reward_system
    )
```

## Beneficios

- **Mejor testabilidad**: Interfaces mockables para pruebas unitarias
- **Mantenibilidad mejorada**: Reducción de acoplamiento
- **Mayor escalabilidad**: Arquitectura modular y extensible
- **Gestión consistente**: Ciclo de vida unificado de servicios
- **Resolución de dependencias**: Eliminación de problemas de dependencias circulares