# Guía de Implementación: Sistema de Transacciones VIP y Puntos

Esta guía explica cómo integrar correctamente el nuevo sistema de transacciones para VIP y puntos en el bot.

## 1. Sistema de Puntos

### 1.1. Estructura del Sistema

El sistema de puntos ahora utiliza transacciones auditables:
- **Modelo**: `PointTransaction` en `database/transaction_models.py`
- **Servicio**: `PointService` en `services/point_service.py`
- **Tabla**: `point_transactions` en la base de datos

### 1.2. Cómo Otorgar Puntos

Para otorgar puntos a un usuario, utiliza el servicio `PointService`:

```python
from services.point_service import PointService

# En un handler o servicio
async def some_handler(message: Message, session: AsyncSession):
    point_service = PointService(session)
    
    # Otorgar 10 puntos con una descripción del origen
    await point_service.add_points(
        user_id=message.from_user.id,
        points=10.0,
        source="message",  # Origen de los puntos
        description="Usuario envió un mensaje"  # Descripción opcional
    )
```

### 1.3. Cómo Deductir Puntos

Para deducir puntos de un usuario:

```python
from services.point_service import PointService

# En un handler o servicio
async def some_handler(message: Message, session: AsyncSession):
    point_service = PointService(session)
    
    # Deduct 5 points
    success = await point_service.deduct_points(
        user_id=message.from_user.id,
        points=5
    )
    
    if success:
        # Puntos deducidos exitosamente
        pass
    else:
        # No hay suficientes puntos o usuario no encontrado
        pass
```

### 1.4. Cómo Verificar el Balance de Puntos

Para obtener el balance actual de puntos de un usuario:

```python
from services.point_service import PointService

# En un handler o servicio
async def some_handler(message: Message, session: AsyncSession):
    point_service = PointService(session)
    
    # Obtener balance
    balance = await point_service.get_balance(user_id=message.from_user.id)
    
    # O también:
    balance = await point_service.get_user_points(user_id=message.from_user.id)
```

### 1.5. Cómo Obtener el Historial de Transacciones

Para obtener el historial de transacciones de un usuario:

```python
from services.point_service import PointService

# En un handler o servicio
async def some_handler(message: Message, session: AsyncSession):
    point_service = PointService(session)
    
    # Obtener historial de transacciones
    transactions = await point_service.get_transaction_history(
        user_id=message.from_user.id
    )
    
    for transaction in transactions:
        print(f"Fecha: {transaction.created_at}")
        print(f"Cantidad: {transaction.amount}")
        print(f"Balance después: {transaction.balance_after}")
        print(f"Origen: {transaction.source}")
        print(f"Descripción: {transaction.description}")
```

## 2. Sistema VIP

### 2.1. Estructura del Sistema

El sistema VIP ahora utiliza transacciones auditables:
- **Modelo**: `VipTransaction` en `database/transaction_models.py`
- **Servicio**: `SubscriptionService` en `services/subscription_service.py`
- **Tabla**: `vip_transactions` en la base de datos

### 2.2. Cómo Otorgar Acceso VIP

Para otorgar acceso VIP a un usuario:

```python
from services.subscription_service import SubscriptionService

# En un handler o servicio
async def some_handler(message: Message, session: AsyncSession):
    subscription_service = SubscriptionService(session)
    
    # Otorgar acceso VIP por 30 días
    await subscription_service.grant_subscription(
        user_id=message.from_user.id,
        duration_days=30,
        source="badge",  # Origen del acceso
        source_id=badge_id  # ID del badge que otorgó el acceso (opcional)
    )
```

### 2.3. Cómo Revocar Acceso VIP

Para revocar el acceso VIP de un usuario:

```python
from services.subscription_service import SubscriptionService

# En un handler o servicio
async def some_handler(message: Message, session: AsyncSession):
    subscription_service = SubscriptionService(session)
    
    # Revocar acceso VIP
    await subscription_service.revoke_subscription(
        user_id=message.from_user.id
    )
```

### 2.4. Cómo Verificar el Estado VIP

Para verificar si un usuario tiene acceso VIP activo:

```python
from services.subscription_service import SubscriptionService
from utils.user_roles import is_vip_member

# En un handler o servicio
async def some_handler(message: Message, session: AsyncSession):
    # Método 1: Usando SubscriptionService
    subscription_service = SubscriptionService(session)
    subscription = await subscription_service.get_subscription(
        user_id=message.from_user.id
    )
    
    if subscription and subscription.is_active:
        # Usuario tiene acceso VIP activo
        expires_at = subscription.expires_at
        pass
    else:
        # Usuario no tiene acceso VIP activo
        pass
    
    # Método 2: Usando utilidad directa
    is_vip = await is_vip_member(message.from_user.id, session)
    if is_vip:
        # Usuario tiene acceso VIP
        pass
```

### 2.5. Cómo Extender la Duración del Acceso VIP

Para extender la duración del acceso VIP de un usuario:

```python
from services.subscription_service import SubscriptionService

# En un handler o servicio
async def some_handler(message: Message, session: AsyncSession):
    subscription_service = SubscriptionService(session)
    
    # Extender acceso VIP por 15 días adicionales
    await subscription_service.extend_subscription(
        user_id=message.from_user.id,
        days=15
    )
```

### 2.6. Cómo Obtener el Historial de Transacciones VIP

Para obtener el historial de transacciones VIP de un usuario:

```python
from services.subscription_service import SubscriptionService

# En un handler o servicio
async def some_handler(message: Message, session: AsyncSession):
    subscription_service = SubscriptionService(session)
    
    # Obtener historial de transacciones VIP
    transactions = await subscription_service.get_transaction_history(
        user_id=message.from_user.id
    )
    
    for transaction in transactions:
        print(f"Fecha: {transaction.created_at}")
        print(f"Acción: {transaction.action}")
        print(f"Origen: {transaction.source}")
        print(f"Duración: {transaction.duration_days}")
        print(f"Expira: {transaction.expires_at}")
        print(f"Notas: {transaction.notes}")
```

## 3. Consideraciones Importantes

### 3.1. Auditoría Automática

Ambos sistemas (puntos y VIP) crean automáticamente registros de transacciones:
- Cada operación de puntos crea una entrada en `point_transactions`
- Cada operación VIP crea una entrada en `vip_transactions`

### 3.2. No Usar Modelos Antiguos

Los siguientes modelos han sido eliminados y no deben usarse:
- `SubscriptionPlan`
- `SubscriptionToken`
- `Token`
- `Tariff`
- `VipAccess`

### 3.3. Compatibilidad de Interfaces

Aunque el sistema interno ha cambiado, las interfaces públicas de los servicios mantienen la misma firma para compatibilidad:
- `PointService.add_points()` mantiene la misma interfaz
- `PointService.deduct_points()` mantiene la misma interfaz
- `SubscriptionService` mantiene interfaces similares

### 3.4. Manejo de Errores

Ambos servicios incluyen manejo de errores apropiado:
- `PointService` verifica que el usuario exista antes de otorgar puntos
- `SubscriptionService` maneja correctamente las fechas de expiración
- Ambos servicios registran errores en el log cuando ocurren

## 4. Ejemplo Completo de Integración

```python
from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from services.point_service import PointService
from services.subscription_service import SubscriptionService
from utils.user_roles import is_vip_member

router = Router()

@router.message(F.text == "/daily_reward")
async def daily_reward(message: Message, session: AsyncSession):
    """Ejemplo de handler que otorga puntos y acceso VIP"""
    
    user_id = message.from_user.id
    
    # Verificar si el usuario ya recibió su recompensa hoy
    # (Implementación específica omitida por brevedad)
    
    # Otorgar puntos
    point_service = PointService(session)
    await point_service.add_points(
        user_id=user_id,
        points=50.0,
        source="daily_reward",
        description="Recompensa diaria"
    )
    
    # Verificar si el usuario tiene acceso VIP
    is_vip = await is_vip_member(user_id, session)
    
    if not is_vip:
        # Otorgar acceso VIP temporal por 7 días
        subscription_service = SubscriptionService(session)
        await subscription_service.grant_subscription(
            user_id=user_id,
            duration_days=7,
            source="daily_reward",
            notes="Recompensa VIP por login diario"
        )
    
    # Enviar mensaje de confirmación al usuario
    await message.answer(
        "¡Recompensa diaria reclamada!\n"
        "Has recibido 50 puntos.\n"
        "Has recibido 7 días de acceso VIP."
    )
```

## 5. Archivos Clave

- `database/transaction_models.py` - Modelos de transacciones
- `services/point_service.py` - Servicio de puntos
- `services/subscription_service.py` - Servicio de suscripciones VIP
- `utils/user_roles.py` - Utilidades para verificar roles
- `database/setup.py` - Inicialización de la base de datos

Esta guía proporciona todos los elementos necesarios para integrar correctamente el sistema de transacciones en nuevas funcionalidades del bot.