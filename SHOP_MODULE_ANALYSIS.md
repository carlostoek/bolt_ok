# Análisis Exhaustivo del Módulo de Tienda

## 1. ANÁLISIS DEL COORDINADOR CENTRAL

### Estructura Actual del CoordinadorCentral
**Archivo**: `services/coordinador_central.py`

**Arquitectura Identificada**:
- **Patrón Facade**: Orquesta interacciones entre subsistemas
- **Enum de Acciones**: `AccionUsuario` define tipos de flujos disponibles
- **Servicios de Integración**: 
  - `ChannelEngagementService`
  - `NarrativePointService` 
  - `NarrativeAccessService`
- **Servicios Base**:
  - `NarrativeService`
  - `PointService`
  - `EmotionalAnalysisService` (opcional)
  - `CharacterVoiceService`

### Puntos de Integración Identificados

#### Para Publicar el Módulo de Tienda:
1. **Nuevo Enum**: Agregar `COMPRAR_ARTICULO` a `AccionUsuario`
2. **Nuevo Servicio de Integración**: `ShopIntegrationService`
3. **Nuevo Flujo**: `_flujo_comprar_articulo()` en CoordinadorCentral

#### Para Suscribirse a Eventos:
- **Eventos a Escuchar**: Cambios en puntos de usuario, actualizaciones de rol VIP
- **Eventos a Emitir**: Compra exitosa, desbloqueo de pistas, cambios en inventario

### Modificaciones Requeridas en CoordinadorCentral:
```python
# Agregar a AccionUsuario enum
COMPRAR_ARTICULO = "comprar_articulo"
LISTAR_TIENDA = "listar_tienda"

# Nuevo servicio de integración
from .integration.shop_integration_service import ShopIntegrationService
self.shop_integration = ShopIntegrationService(session)

# Nuevos flujos
async def _flujo_comprar_articulo(self, user_id: int, **kwargs) -> Dict[str, Any]
async def _flujo_listar_tienda(self, user_id: int, **kwargs) -> Dict[str, Any]
```

## 2. ANÁLISIS DEL SISTEMA DE MENÚS

### Arquitectura Actual de Menús
**Archivos Clave**:
- `utils/menu_factory.py`: Factory para crear menús basados en rol
- `utils/menu_manager.py`: Gestión de ciclo de vida de mensajes
- `keyboards/`: Teclados específicos por funcionalidad

### Integración de Botón de Tienda

#### Modificaciones Necesarias:
1. **MenuFactory**: Agregar estado `"shop"` y `"shop_item_details"`
2. **Teclados Principales**: Agregar botón "🛒 Tienda" en menús VIP y Free
3. **Nuevo Teclado**: `keyboards/shop_kb.py` para navegación de tienda

#### Ubicación del Botón:
- **Menú VIP**: Entre "🎁 Recompensas" y "🏛️ Subastas"
- **Menú Free**: Como nueva opción principal
- **Menú Admin**: Opción de gestión de tienda

## 3. ANÁLISIS DE INTEGRACIONES Y MODIFICACIONES

### 3.1 Integración con Gamificación

#### Puntos de Conexión Identificados:
- **PointService**: Consultar saldo, descontar puntos en compras
- **UserService**: Verificar existencia y rol del usuario
- **AchievementService**: Otorgar logros por compras

#### Modificaciones Requeridas:
```python
# En PointService - agregar método
async def deduct_points_for_purchase(self, user_id: int, amount: float, item_id: str) -> bool

# En AchievementService - nuevos logros
SHOP_ACHIEVEMENTS = [
    {"id": "first_purchase", "name": "Primera Compra", ...},
    {"id": "big_spender", "name": "Gran Comprador", ...}
]
```

### 3.2 Integración con Narrativa

#### Puntos de Conexión Identificados:
- **NarrativeService**: Desbloquear pistas específicas
- **LorePieceService**: Gestionar pistas desbloqueadas por compras

#### Modificaciones Requeridas:
```python
# Nuevo campo en modelo ShopItem
unlocks_lore_piece_code = Column(String, nullable=True)

# Integración en flujo de compra
if item.unlocks_lore_piece_code:
    await self.narrative_service.unlock_lore_piece(user_id, item.unlocks_lore_piece_code)
```

### 3.3 Integración con Administración de Canales

#### Puntos de Conexión Identificados:
- **ConfigService**: Verificar configuración de canales VIP
- **SubscriptionService**: Verificar estatus VIP para productos exclusivos

#### Modificaciones Requeridas:
```python
# En ShopService
async def can_access_vip_items(self, user_id: int) -> bool:
    return await self.subscription_service.is_subscription_active(user_id)
```

## 4. EVALUACIÓN DE MODIFICACIONES NECESARIAS

### 4.1 Nuevos Componentes a Agregar

#### Base de Datos:
```sql
-- Nueva tabla para artículos de tienda
CREATE TABLE shop_items (
    id INTEGER PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT,
    price INTEGER NOT NULL,  -- En besitos/visitos
    category VARCHAR,
    is_vip_exclusive BOOLEAN DEFAULT FALSE,
    unlocks_lore_piece_code VARCHAR,
    image_url VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    stock_quantity INTEGER DEFAULT -1,  -- -1 = ilimitado
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla para compras de usuarios
CREATE TABLE user_purchases (
    id INTEGER PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    item_id INTEGER REFERENCES shop_items(id),
    price_paid INTEGER NOT NULL,
    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, item_id)  -- Prevenir compras duplicadas
);

-- Tabla para inventario de usuario
CREATE TABLE user_inventory (
    user_id BIGINT REFERENCES users(id),
    item_id INTEGER REFERENCES shop_items(id),
    quantity INTEGER DEFAULT 1,
    acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(user_id, item_id)
);
```

#### Servicios Nuevos:
1. **ShopService**: Lógica principal de tienda
2. **ShopIntegrationService**: Integración con coordinador
3. **InventoryService**: Gestión de inventario de usuario

#### Handlers Nuevos:
1. **ShopHandler**: Manejo de comandos de tienda
2. **AdminShopHandler**: Gestión administrativa de tienda

### 4.2 Componentes Existentes a Modificar

#### CoordinadorCentral:
- Agregar nuevos enums de acción
- Agregar nuevos flujos de tienda
- Integrar ShopIntegrationService

#### MenuFactory:
- Agregar estados de menú de tienda
- Integrar con teclados de tienda

#### Teclados Principales:
- Agregar botón de tienda en menús principales
- Crear navegación específica de tienda

### 4.3 Riesgos y Consideraciones

#### Consistencia de Datos:
- **Transacciones Atómicas**: Compras deben ser atómicas (descuento + inventario + pista)
- **Validación de Stock**: Prevenir overselling en artículos limitados
- **Rollback**: Mecanismo para revertir compras fallidas

#### Escalabilidad:
- **Concurrencia**: Múltiples usuarios comprando simultáneamente
- **Cache**: Cache de artículos para reducir consultas DB
- **Paginación**: Para tiendas con muchos artículos

#### Seguridad:
- **Validación de Precios**: Prevenir manipulación de precios
- **Verificación de Permisos**: Solo admins pueden gestionar tienda
- **Audit Trail**: Registro de todas las transacciones

## 5. REVISIÓN DE CONCEPTO.MD

### Integraciones Documentadas:

#### Tabla de Acciones del Usuario (concepto.md):
| Acción | Narrativa | Gamificación | Administración |
|--------|-----------|--------------|----------------|
| Compra en tienda | Desbloquea fragmento | Usa besitos | — |

#### Conexiones Identificadas:
- **Narrativa**: Algunos objetos de mochila desbloquean fragmentos ocultos
- **Gamificación**: Besitos como moneda, objetos en mochila personal
- **Administración**: Control de acceso VIP para productos exclusivos

### Discrepancias Encontradas:
1. **Terminología**: Concepto usa "besitos", código actual usa "points"
2. **Mochila**: Concepto menciona mochila para objetos comprados, código actual tiene mochila para pistas narrativas
3. **Integración**: Concepto sugiere integración más profunda de la que existe actualmente

## 6. PLAN DE IMPLEMENTACIÓN DETALLADO

### Fase 1: Modelos de Base de Datos
1. Crear modelos para `ShopItem`, `UserPurchase`, `UserInventory`
2. Migración de base de datos
3. Índices para performance

### Fase 2: Servicios Core
1. **ShopService**: CRUD de artículos, lógica de compra
2. **InventoryService**: Gestión de inventario de usuario
3. **ShopIntegrationService**: Integración con coordinador

### Fase 3: Integración con Coordinador
1. Agregar enums de acción
2. Implementar flujos de tienda
3. Integrar servicios de tienda

### Fase 4: Handlers y UI
1. **ShopHandler**: Comandos de usuario
2. **AdminShopHandler**: Gestión administrativa
3. **Teclados**: Navegación de tienda
4. **MenuFactory**: Estados de tienda

### Fase 5: Integraciones Específicas
1. **Gamificación**: Integrar con PointService
2. **Narrativa**: Integrar desbloqueo de pistas
3. **VIP**: Integrar verificación de suscripción

### Fase 6: Testing y Validación
1. Tests unitarios para servicios
2. Tests de integración
3. Validación end-to-end

## 7. ARQUITECTURA PROPUESTA

### Flujo de Compra:
```
Usuario → Handler → CoordinadorCentral → ShopIntegrationService → ShopService
                                      ↓
                  PointService ← NarrativeService ← InventoryService
```

### Eventos del Sistema:
```
EVENTOS EMITIDOS POR TIENDA:
- item_purchased(user_id, item_id, price)
- lore_piece_unlocked(user_id, lore_code)
- inventory_updated(user_id, item_id, quantity)

EVENTOS ESCUCHADOS POR TIENDA:
- user_points_updated(user_id, new_balance)
- user_vip_status_changed(user_id, is_vip)
- user_level_changed(user_id, new_level)
```

## 8. CONCLUSIONES DEL ANÁLISIS

### Viabilidad: ✅ ALTA
- El sistema actual tiene la arquitectura necesaria para soportar el módulo de tienda
- El CoordinadorCentral está diseñado para este tipo de integraciones
- Los servicios existentes proporcionan las APIs necesarias

### Complejidad: 🟡 MEDIA-ALTA
- Requiere modificaciones en múltiples componentes
- Necesita nuevos modelos de base de datos
- Integración con 3 módulos principales

### Riesgos: 🟡 CONTROLABLES
- Transacciones atómicas críticas para consistencia
- Concurrencia en compras simultáneas
- Integración con sistema de pistas narrativas

### Tiempo Estimado: 2-3 días
- Día 1: Modelos, servicios core, integración básica
- Día 2: Handlers, UI, integraciones específicas
- Día 3: Testing, refinamiento, documentación

## 9. PRÓXIMOS PASOS

✅ **ANÁLISIS COMPLETADO**

**Listo para implementación**:
1. Todos los puntos de integración identificados
2. Modificaciones necesarias documentadas
3. Riesgos evaluados y mitigados
4. Arquitectura validada contra concepto.md

**Proceder con implementación siguiendo el plan detallado.**