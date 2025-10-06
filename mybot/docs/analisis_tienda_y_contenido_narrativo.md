# Análisis del Sistema de Tienda y Desbloqueo de Contenido Narrativo

**Fecha:** 30 de septiembre de 2025
**Solicitado por:** Usuario
**Objetivo:** Analizar el módulo de tienda existente y el sistema de desbloqueo de contenido narrativo para diseñar un panel de administración

---

## 📋 Resumen Ejecutivo

El sistema actual tiene una **tienda funcional** con dos productos de prueba que desbloquean contenido narrativo. La arquitectura está bien diseñada pero **necesita un panel de administración** para gestionar productos y sus relaciones con contenido narrativo protegido.

### Hallazgos Clave:
✅ **Sistema funcional** de compra y desbloqueo
✅ **Relación establecida** entre productos y contenido narrativo
⚠️ **Falta panel de administración** para gestionar la tienda
⚠️ **Sistema de condiciones** mixto (necesita unificación)
✅ **Integración completa** con coordinador central y mochila narrativa

---

## 🗂️ Componentes Analizados

### 1. **Modelos de Base de Datos** (`database/models.py`)

#### `ShopItem` (Línea 472)
```python
class ShopItem(Base):
    __tablename__ = "shop_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(Integer, nullable=False)  # Precio en besitos
    is_vip_only = Column(Boolean, default=False)
    unlocks_lore_piece_id = Column(Integer, ForeignKey("lore_pieces.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    lore_piece = relationship("LorePiece")
```

**✅ Puntos fuertes:**
- Relación directa con `LorePiece` para desbloqueo
- Campo `is_vip_only` para productos exclusivos
- Campo `is_active` para activar/desactivar productos
- Precio en "besitos" (puntos del sistema)

**⚠️ Limitaciones identificadas:**
- Solo soporta relación 1:1 con contenido narrativo
- No hay campo para condiciones compuestas (ej: "50 besitos Y otro producto")
- No hay campo para límite de stock o compras por usuario
- No hay campo para imagen del producto

#### `UserPurchase` (Línea 486)
```python
class UserPurchase(Base):
    __tablename__ = "user_purchases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    shop_item_id = Column(Integer, ForeignKey("shop_items.id"), nullable=False)
    purchased_at = Column(DateTime, default=func.now())
    price_paid = Column(Integer, nullable=False)

    user = relationship("User", back_populates="purchases")
    shop_item = relationship("ShopItem")
```

**✅ Puntos fuertes:**
- Historial completo de compras
- Registro del precio pagado (útil si cambian precios)

#### `LorePiece` (Línea 452)
```python
class LorePiece(Base):
    __tablename__ = "lore_pieces"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code_name = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    content_type = Column(String, nullable=False)  # text, image, audio, video
    content = Column(Text, nullable=False)
    category = Column(String, nullable=True)  # fragmentos, memorias, secretos, llaves
    is_main_story = Column(Boolean, default=False)
    unlock_condition_type = Column(String, nullable=True)  # ⚠️ Sistema antiguo
    unlock_condition_value = Column(String, nullable=True)  # ⚠️ Sistema antiguo
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
```

**⚠️ Sistema de condiciones DUAL detectado:**
1. **Sistema nuevo:** Relación `ShopItem.unlocks_lore_piece_id`
2. **Sistema antiguo:** Campos `unlock_condition_type` y `unlock_condition_value`

**Ejemplo del sistema antiguo en uso:**
```python
# shop_service.py línea 107
unlock_condition_type="requires_item",
unlock_condition_value="diario_intimo"
```

#### `UserLorePiece` (Línea 498)
```python
class UserLorePiece(Base):
    __tablename__ = "user_lore_pieces"

    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    lore_piece_id = Column(Integer, ForeignKey("lore_pieces.id"), primary_key=True)
    unlocked_at = Column(DateTime, default=func.now())
    context = Column(JSON, nullable=True)  # 🔥 Campo flexible para metadata
```

**✅ Campo `context` (JSON):** Permite almacenar metadata rica sobre cómo se desbloqueó:
```python
context={
    'source': 'shop_purchase',
    'item_id': item_id,
    'item_name': shop_item.name,
    'purchased_at': datetime.utcnow().isoformat()
}
```

---

### 2. **Servicios**

#### `ShopService` (`services/shop_service.py`)

**Funciones principales:**

1. **`get_available_items(user_id)`** (Línea 20)
   - Filtra productos por estado VIP del usuario
   - Auto-crea productos de prueba si no existen
   - ✅ Respeta `is_active` y `is_vip_only`

2. **`purchase_item(user_id, item_id)`** (Línea 147)
   - Valida puntos del usuario
   - Valida estado VIP para productos exclusivos
   - Deduce puntos ("besitos")
   - Registra compra en `UserPurchase`
   - **Desbloquea contenido narrativo** automáticamente

3. **`_add_to_backpack(user_id, item_id, shop_item)`** (Línea 200)
   - Agrega el `LorePiece` a la mochila del usuario
   - Verifica que no esté duplicado
   - Registra metadata en el campo `context`

4. **`_ensure_diario_diana_item_exists()`** (Línea 52) ⚠️
5. **`_ensure_diario_intimo_item_exists()`** (Línea 91) ⚠️

**⚠️ PROBLEMA:** Productos hardcodeados en el servicio. Deberían crearse vía panel de admin.

---

#### `CoordinadorCentral` (`services/coordinador_central.py`)

**Flujos de tienda:**

1. **`_flujo_acceder_tienda(user_id)`** (Línea 674)
   - Wrapper sobre `ShopService.get_available_items()`
   - Serializa productos para el frontend

2. **`_flujo_comprar_item(user_id, item_id)`** (Línea 709)
   - Wrapper sobre `ShopService.purchase_item()`
   - Maneja errores y retorna resultado estandarizado

✅ **Integración limpia** con el coordinador central.

---

### 3. **Handlers** (`handlers/shop_handlers.py`)

```python
@router.callback_query(F.data == "shop_access")
async def show_shop(callback: CallbackQuery, session: AsyncSession):
    coordinador = CoordinadorCentral(session)
    result = await coordinador.ejecutar_flujo(
        callback.from_user.id,
        AccionUsuario.ACCEDER_TIENDA
    )
    # ... muestra teclado con productos

@router.callback_query(F.data.startswith("buy_item:"))
async def handle_purchase(callback: CallbackQuery, session: AsyncSession):
    item_id = int(callback.data.split(":")[1])
    coordinador = CoordinadorCentral(session)
    result = await coordinador.ejecutar_flujo(
        user_id,
        AccionUsuario.COMPRAR_ITEM,
        item_id=item_id
    )
    # ... notifica resultado
```

✅ **Handlers simples y limpios** que delegan toda la lógica al coordinador.

---

### 4. **Sistema de Mochila Narrativa** (`backpack.py`)

Este módulo maneja la visualización y combinación de contenido narrativo desbloqueado.

**Categorías de contenido narrativo:**
```python
BACKPACK_CATEGORIES = {
    'fragmentos': '🗺️ Fragmentos del Mapa',
    'memorias': '💭 Memorias Compartidas',
    'secretos': '🔮 Secretos del Diván',
    'llaves': '🗝️ Llaves de Acceso'
}
```

**Función clave: `desbloquear_pista_narrativa()`** (Línea 520)
- Busca el `LorePiece` por `code_name`
- Verifica que el usuario no lo tenga ya
- Crea registro en `UserLorePiece` con `context`
- Envía notificación narrativa al usuario

✅ **Sistema completo** de visualización, organización y combinación de pistas.

---

## 🔍 Productos de Verificación Existentes

### Producto 1: "📖 Diario Secreto"

**Creado en:** `shop_service.py:52`

```python
# LorePiece
LorePiece(
    title="Diario Secreto de Diana",
    code_name="diario_secreto_diana",
    content="Contenido exclusivo del diario secreto de Diana...",
    content_type="text",
    unlock_conditions={"requires_item": "diario_diana"}  # ⚠️ Sistema antiguo
)

# ShopItem
ShopItem(
    name="📖 Diario Secreto",
    description="Un diario personal de Diana que desbloquea contenido exclusivo",
    price=50,  # besitos
    is_vip_only=False,
    is_active=True,
    unlocks_lore_piece_id=lore_piece.id  # ✅ Sistema nuevo
)
```

### Producto 2: "📓 Diario Íntimo"

**Creado en:** `shop_service.py:91`

```python
# LorePiece
LorePiece(
    title="Diario Íntimo de Diana",
    code_name="diario_intimo_diana",
    content="Acceso exclusivo al contenido más íntimo de Diana...",
    content_type="text",
    unlock_condition_type="requires_item",  # ⚠️ Sistema antiguo
    unlock_condition_value="diario_intimo"  # ⚠️ Sistema antiguo
)

# ShopItem
ShopItem(
    name="📓 Diario Íntimo",
    description="El diario personal más íntimo de Diana...",
    price=30,  # besitos
    is_vip_only=False,
    is_active=True,
    unlocks_lore_piece_id=lore_piece.id  # ✅ Sistema nuevo
)
```

---

## ⚠️ Problemas y Limitaciones Identificados

### 1. **Sistema de Condiciones Dual (Conflicto)**

**Problema:** Existen DOS sistemas para manejar condiciones de desbloqueo:

- **Sistema 1 (Nuevo):** Relación `ShopItem.unlocks_lore_piece_id → LorePiece`
- **Sistema 2 (Antiguo):** Campos `LorePiece.unlock_condition_type` y `unlock_condition_value`

**Ejemplo del conflicto:**
```python
# El Diario Íntimo usa AMBOS sistemas:
unlock_condition_type="requires_item",  # Sistema antiguo
unlock_condition_value="diario_intimo"  # Sistema antiguo
# Y también:
unlocks_lore_piece_id=lore_piece.id  # Sistema nuevo
```

**Impacto:**
- Confusión sobre qué sistema usar
- Potencial para bugs si no se sincronizan
- Dificulta la implementación de condiciones compuestas

**Recomendación:** Unificar en un solo sistema con soporte para condiciones compuestas.

---

### 2. **Productos Hardcodeados en el Servicio**

**Problema:** Los productos de prueba se crean automáticamente en el servicio:
- `_ensure_diario_diana_item_exists()` (línea 52)
- `_ensure_diario_intimo_item_exists()` (línea 91)

**Impacto:**
- No hay flexibilidad para crear productos sin modificar código
- Violación del principio de separación de responsabilidades
- Dificulta testing y desarrollo

**Recomendación:** Mover esta lógica a un panel de administración.

---

### 3. **Falta de Condiciones Compuestas**

**Limitación actual:** Un producto solo puede desbloquear **1 pieza narrativa**.

**Casos de uso no soportados:**
- "Desbloquear si tienes el Producto A **Y** el Producto B"
- "Desbloquear si tienes 100 besitos **Y** el Producto A"
- "Desbloquear si tienes el Producto A **O** 200 besitos"
- "Desbloquear 3 piezas narrativas al comprar 1 producto"

**Recomendación:** Diseñar un sistema de condiciones flexible tipo JSON:
```json
{
  "type": "AND",
  "conditions": [
    {"type": "item", "item_id": 1},
    {"type": "points", "amount": 50}
  ]
}
```

---

### 4. **Sin Gestión de Inventario o Límites**

**Limitaciones:**
- No hay límite de stock por producto
- No hay límite de compras por usuario
- No se verifica si el usuario ya compró el producto
- No hay productos "consumibles" vs "permanentes"

---

### 5. **Sin Imágenes o Media para Productos**

**Limitación:** Los productos solo tienen texto (`name` y `description`).

**Recomendación:** Agregar campo `image_file_id` para mostrar imagen del producto en la tienda.

---

## ✅ Fortalezas del Sistema Actual

### 1. **Arquitectura Limpia**
- Separación clara de responsabilidades
- Patrón de servicio bien implementado
- Integración con coordinador central

### 2. **Sistema de Mochila Completo**
- Categorización de contenido narrativo
- Sistema de combinación de pistas
- Visualización organizada
- Metadata rica con campo `context`

### 3. **Validaciones Sólidas**
- Verifica puntos antes de comprar
- Verifica estado VIP para productos exclusivos
- Evita duplicados en la mochila
- Maneja errores gracefully

### 4. **Experiencia de Usuario**
- Notificaciones narrativas al desbloquear contenido
- Mensajes contextuales según la fuente de desbloqueo
- Integración con el sistema de personajes (Diana, Lucien)

---

## 🎯 Recomendaciones para el Panel de Administración

### Funcionalidades Esenciales

#### 1. **CRUD de Productos**
- ✅ Crear producto nuevo
- ✅ Editar producto existente
- ✅ Activar/Desactivar producto
- ✅ Eliminar producto (soft delete)
- ✅ Ver historial de ventas por producto

#### 2. **Configuración de Desbloqueo de Contenido**
- ✅ Seleccionar qué `LorePiece` desbloquea el producto
- ✅ Opción de no desbloquear nada (producto decorativo)
- ✅ Vista previa del contenido que se desbloqueará
- ✅ Selector de múltiples piezas narrativas (desbloqueo múltiple)

#### 3. **Sistema de Condiciones Avanzadas** (Fase 2)
- ⚠️ Definir condiciones compuestas para desbloqueo
- ⚠️ Condiciones tipo AND/OR/NOT
- ⚠️ Condiciones por: producto, besitos, nivel, estado VIP
- ⚠️ Validador visual de condiciones

#### 4. **Gestión de Inventario**
- ✅ Precio en besitos
- ✅ Marcar como VIP-only
- ✅ Límite de stock (opcional)
- ✅ Límite de compras por usuario (opcional)
- ✅ Fecha de inicio/fin de disponibilidad (opcional)

#### 5. **Preview y Testing**
- ✅ Vista previa de cómo se ve el producto en la tienda
- ✅ Botón "Comprar como prueba" (sin gastar puntos reales)
- ✅ Simulador de compra

#### 6. **Reportes y Analytics**
- ✅ Productos más vendidos
- ✅ Ingresos totales (besitos)
- ✅ Productos sin ventas
- ✅ Tasa de conversión por producto

---

## 📐 Propuesta de Estructura de Datos Mejorada

### Opción 1: Extender el modelo actual

```python
class ShopItem(Base):
    # ... campos existentes ...

    # NUEVOS CAMPOS:
    image_file_id = Column(String, nullable=True)  # Telegram file_id
    stock_limit = Column(Integer, nullable=True)  # None = ilimitado
    purchase_limit_per_user = Column(Integer, nullable=True)  # None = ilimitado
    available_from = Column(DateTime, nullable=True)
    available_until = Column(DateTime, nullable=True)
    unlock_conditions = Column(JSON, nullable=True)  # Sistema de condiciones flexible

    # Para múltiples desbloqueos:
    # Reemplazar: unlocks_lore_piece_id (ForeignKey)
    # Por: lore_pieces = relationship("LorePiece", secondary="shop_item_lore_pieces")
```

### Opción 2: Tabla intermedia (recomendado)

```python
class ShopItemLorePiece(Base):
    """Relación many-to-many entre productos y contenido narrativo"""
    __tablename__ = "shop_item_lore_pieces"

    shop_item_id = Column(Integer, ForeignKey("shop_items.id"), primary_key=True)
    lore_piece_id = Column(Integer, ForeignKey("lore_pieces.id"), primary_key=True)
    unlock_conditions = Column(JSON, nullable=True)  # Condiciones específicas
    created_at = Column(DateTime, default=func.now())
```

**Ventajas:**
- Soporta desbloqueo múltiple (1 producto → N piezas)
- Condiciones por relación (no por entidad)
- Histórico de relaciones
- Más flexible para futuras extensiones

---

## 🚀 Plan de Implementación Sugerido

### Fase 1: Panel Básico (MVP)
1. CRUD de productos (nombre, descripción, precio, is_vip_only, is_active)
2. Selector simple de `LorePiece` (1:1)
3. Tabla de visualización de productos
4. Activar/Desactivar productos
5. Eliminar productos (soft delete)

### Fase 2: Condiciones Avanzadas
1. Migrar a tabla intermedia `ShopItemLorePiece`
2. Implementar sistema de condiciones JSON
3. UI para configurar condiciones compuestas
4. Validador de condiciones

### Fase 3: Analytics y Gestión Avanzada
1. Reportes de ventas
2. Límites de stock y compras
3. Programación de disponibilidad
4. Imágenes de productos
5. Vista previa y testing

---

## 📊 Diagrama de Flujo Actual

```
Usuario → [shop_access] → ShopHandler → CoordinadorCentral → ShopService
                                                                    ↓
                                                            get_available_items()
                                                                    ↓
                                                            Filtra por VIP/Activo
                                                                    ↓
                                                            Retorna productos
                                                                    ↓
Usuario selecciona → [buy_item:123] → ShopHandler → CoordinadorCentral → ShopService
                                                                                ↓
                                                                      purchase_item()
                                                                                ↓
                                                                      Valida puntos/VIP
                                                                                ↓
                                                                      Deduce besitos
                                                                                ↓
                                                                      Registra compra
                                                                                ↓
                                                                    _add_to_backpack()
                                                                                ↓
                                                                  Crea UserLorePiece
                                                                                ↓
                                                              Notifica al usuario ✅
```

---

## 🔗 Archivos Relevantes

| Archivo | Descripción | Líneas clave |
|---------|-------------|--------------|
| `database/models.py` | Definición de modelos | 452-510 |
| `services/shop_service.py` | Lógica de tienda | 1-235 |
| `handlers/shop_handlers.py` | Handlers de UI | 1-64 |
| `services/coordinador_central.py` | Integración | 674-729 |
| `backpack.py` | Sistema de mochila | 520-563 |
| `keyboards/common.py` | UI de tienda | `build_shop_keyboard()` |

---

## 🎬 Conclusión

El sistema de tienda **funciona correctamente** y tiene una base sólida. Los principales desafíos son:

1. ⚠️ **Unificar el sistema de condiciones** (dual → simple)
2. ⚠️ **Eliminar productos hardcodeados** del servicio
3. ✅ **Crear panel de administración** para gestión visual
4. ✅ **Extender modelo** para soportar condiciones compuestas

**Prioridad 1:** Panel de administración básico (CRUD)
**Prioridad 2:** Sistema de condiciones avanzadas
**Prioridad 3:** Analytics y features adicionales

El sistema está **listo para ser administrado visualmente** con mínimos cambios en la arquitectura actual.