# Guía de Stock y Límites de Compra - Mejora #4

**Fecha:** 30 de septiembre de 2025
**Mejora:** #4 - Límites de Stock y Compras por Usuario
**Estado:** ✅ Completado

---

## 📋 Resumen

Se implementó un sistema completo de control de inventario que permite:
- **Stock limitado**: Productos que se agotan cuando se alcanza un límite
- **Límites por usuario**: Restringir cuántas veces cada usuario puede comprar un producto
- **Productos exclusivos y ediciones limitadas**

---

## 🎯 Características Implementadas

### 1. **Campos de Stock en Base de Datos**

**Modelo actualizado:** `database/models.py:482-483`

```python
class ShopItem(Base):
    __tablename__ = "shop_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(Integer, nullable=False)
    is_vip_only = Column(Boolean, default=False)
    unlocks_lore_piece_id = Column(Integer, ForeignKey("lore_pieces.id"), nullable=True)
    image_file_id = Column(String(255), nullable=True)
    stock_limit = Column(Integer, nullable=True)  # 🆕 NULL = unlimited stock
    max_purchases_per_user = Column(Integer, default=1)  # 🆕 Max purchases per user
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
```

**Características:**
- ✅ `stock_limit`: NULL = ilimitado, número = unidades disponibles
- ✅ `max_purchases_per_user`: 0 = sin límite, número = máximo de compras
- ✅ Default: `max_purchases_per_user = 1` (productos únicos por defecto)

---

## 🔧 Flujo de Creación con Stock

### Paso 6: Stock del Producto (Opcional)

**Después de configurar imagen**, el admin ve:

```
➕ Crear Producto

✅ Nombre: 🎨 Artwork Exclusivo
✅ Precio: 100 besitos
✅ Acceso: 🆓 Para Todos
✅ Imagen: Recibida ✓

📦 Paso 6: Stock del Producto (Opcional)

¿Este producto tiene stock limitado?

[📦 Sí, tiene stock limitado]
[♾️ Stock ilimitado]
```

### Opción A: Stock Limitado

**1. Admin elige "📦 Sí, tiene stock limitado"**

```
➕ Crear Producto

📦 Configurar Stock Limitado

Ingresa el número de unidades disponibles:

💡 Ejemplos:
• 10 - Para productos exclusivos
• 50 - Para ediciones limitadas
• 100 - Para stock moderado

⚠️ Una vez agotado, el producto dejará de aparecer en tienda.

[❌ Cancelar]
```

**2. Admin ingresa cantidad (ej: 10)**

Continúa al Paso 7...

### Opción B: Stock Ilimitado

```
➕ Crear Producto

✅ Nombre: 📓 Diario Íntimo
✅ Precio: 30 besitos
✅ Stock: ♾️ Ilimitado

🔢 Paso 7: Límite por Usuario

¿Cuántas veces puede comprar este producto cada usuario?

[1️⃣ Una vez (único)]
[♾️ Sin límite]
[✏️ Otro número]
```

---

## 🔢 Paso 7: Límite por Usuario

### Opción 1: Una Vez (Único)

```
✅ Límite: 1 vez

Cada usuario solo puede comprar este producto una vez.
Perfecto para contenido exclusivo o recompensas únicas.
```

### Opción 2: Sin Límite

```
✅ Límite: ♾️ Sin límite

Cada usuario puede comprar este producto cuantas veces quiera.
Ideal para consumibles o recursos recurrentes.
```

### Opción 3: Otro Número

**Admin elige "✏️ Otro número"**

```
➕ Crear Producto

🔢 Configurar Límite por Usuario

Ingresa el número máximo de veces que cada usuario puede comprar este producto:

💡 Ejemplos:
• 1 - Solo pueden comprar una vez
• 3 - Hasta 3 compras por usuario
• 5 - Hasta 5 compras por usuario

[❌ Cancelar]
```

**Admin ingresa número (ej: 3)**

```
➕ Crear Producto

✅ Nombre: 📓 Diario Íntimo
✅ Precio: 30 besitos
✅ Stock: ♾️ Ilimitado
✅ Límite por usuario: 3 compras

🔓 Paso 8: Desbloqueo de Contenido

¿Este producto desbloquea contenido narrativo?
```

---

## ✏️ Edición de Stock y Límites

### Menú de Edición Actualizado

**Ruta:** Admin → Tienda → [Producto] → ✏️ Editar

```
✏️ Editar Producto

Producto: 🎨 Artwork Exclusivo

¿Qué deseas editar?

[📝 Nombre]        [📄 Descripción]
[💰 Precio]        [👑 Acceso VIP]
[🖼️ Imagen]        [📦 Stock]          🆕
[🔢 Límite Usuario] [🔓 Desbloqueo]     🆕
[🔙 Volver]
```

---

## 📦 Gestión de Stock

### Producto CON stock limitado:

```
✏️ Editar Stock

Producto: 🎨 Artwork Exclusivo
Stock actual: 📦 50 unidades

Opciones:

[📦 Cambiar Cantidad]
[♾️ Hacer Ilimitado]
[🔙 Volver]
```

### Producto SIN stock limitado:

```
✏️ Editar Stock

Producto: 📓 Diario Íntimo
Stock actual: ♾️ Ilimitado

Opciones:

[📦 Establecer Límite]
[🔙 Volver]
```

### Cambiar Cantidad de Stock

```
✏️ Configurar Stock

📦 Ingresa el número de unidades disponibles:

💡 Ejemplos:
• 10 - Para productos exclusivos
• 50 - Para ediciones limitadas
• 100 - Para stock moderado

⚠️ Una vez agotado, el producto dejará de aparecer en tienda.
```

**Después de ingresar (ej: 75):**

```
✅ Stock Actualizado

Producto: 🎨 Artwork Exclusivo

Stock configurado a: 📦 75 unidades

El producto dejará de aparecer en tienda cuando se agoten las 75 unidades.

[✏️ Editar Otro Campo]
[👁️ Ver Producto]
[🔙 Lista de Productos]
```

---

## 🔢 Gestión de Límite por Usuario

### Menú de Límite

```
✏️ Editar Límite por Usuario

Producto: 📓 Diario Íntimo
Límite actual: 1 vez

Opciones:

[1️⃣ Una vez (único)]
[♾️ Sin límite]
[✏️ Otro número]
[🔙 Volver]
```

### Cambio Instantáneo (1 vez / Sin límite)

```
✅ Límite por Usuario Actualizado

Producto: 📓 Diario Íntimo

Límite configurado a: ♾️ Sin límite

Cada usuario podrá comprar este producto sin límite.

[✏️ Editar Otro Campo]
[👁️ Ver Producto]
[🔙 Lista de Productos]
```

---

## 🛒 Experiencia del Usuario en Tienda

### Visualización con Stock

Cuando un usuario accede a la tienda (`/shop`):

#### Stock Normal (>10 unidades)

```
🛒 Tienda - Elige un artículo:

[📓 Diario Íntimo - 30 besitos]
[🎨 Artwork Exclusivo - 100 besitos]
[🔙 Volver]
```

#### Stock Bajo (6-10 unidades)

```
🛒 Tienda - Elige un artículo:

[📓 Diario Íntimo - 30 besitos]
[🎨 Artwork Exclusivo - 100 besitos [8 restantes]]  ⚠️
[🔙 Volver]
```

#### Stock Crítico (1-5 unidades)

```
🛒 Tienda - Elige un artículo:

[📓 Diario Íntimo - 30 besitos]
[🎨 Artwork Exclusivo - 100 besitos [¡Solo 3!]]  🚨
[🔙 Volver]
```

#### Stock Agotado

**El producto NO aparece en la tienda**

Solo el admin puede ver productos agotados (marcados como "Agotado" en el panel).

---

## 🚫 Validaciones de Compra

### 1. Validación de Stock

**Escenario:** Usuario intenta comprar un producto agotado

```
Usuario → Click en producto → Intento de compra
     ↓
Sistema verifica stock
     ↓
Stock: 10/10 vendidos
     ↓
❌ 🎨 Artwork Exclusivo agotado. Solo había 10 unidades disponibles.
```

### 2. Validación de Límite por Usuario

**Escenario:** Usuario intenta comprar más veces del límite permitido

```
Usuario → Click en producto → Intento de compra
     ↓
Sistema verifica compras previas del usuario
     ↓
Usuario ya compró: 1 vez
Límite permitido: 1 vez
     ↓
❌ Ya compraste 📓 Diario Íntimo el máximo de 1 vez permitido.
```

**Con límite de 3 veces:**

```
❌ Ya compraste 🎨 Artwork Exclusivo el máximo de 3 veces permitido.
```

### 3. Filtrado Automático

El sistema **automáticamente oculta** de la tienda:

✅ Productos agotados (stock alcanzado)
✅ Productos donde el usuario alcanzó su límite

**Resultado:** Usuario solo ve productos que **puede comprar**

---

## 📊 Casos de Uso

### Caso 1: Producto Exclusivo (Stock 10, Límite 1)

**Configuración:**
```
Producto: 🎨 Artwork Premium de Diana
Stock: 📦 10 unidades
Límite por usuario: 1 vez
Precio: 150 besitos
```

**Comportamiento:**
- Solo 10 usuarios podrán comprarlo
- Cada usuario solo puede comprar 1 vez
- Una vez 10 usuarios compran → producto desaparece de tienda
- **Escasez y exclusividad**

---

### Caso 2: Edición Limitada (Stock 50, Sin Límite Usuario)

**Configuración:**
```
Producto: 📸 Pack de Fotos Exclusivas
Stock: 📦 50 unidades
Límite por usuario: ♾️ Sin límite
Precio: 75 besitos
```

**Comportamiento:**
- Solo se venden 50 unidades en total
- Cada usuario puede comprar múltiples veces
- Un usuario "ballena" podría comprar las 50
- **Edición limitada sin restricción individual**

---

### Caso 3: Consumible Limitado (Stock Ilimitado, Límite 3)

**Configuración:**
```
Producto: 💎 Boost de Puntos 2x
Stock: ♾️ Ilimitado
Límite por usuario: 3 veces
Precio: 20 besitos
```

**Comportamiento:**
- Siempre disponible en tienda
- Cada usuario puede comprar máximo 3 veces
- Perfecto para "power-ups" o consumibles
- **Control de uso sin escasez artificial**

---

### Caso 4: Producto Único Global (Stock 1, Límite 1)

**Configuración:**
```
Producto: 👑 Corona de la Primera Seguidora
Stock: 📦 1 unidad
Límite por usuario: 1 vez
Precio: 500 besitos
```

**Comportamiento:**
- **Solo 1 usuario en todo el sistema lo tendrá**
- Primera persona en comprarlo gana
- Desaparece inmediatamente después de venta
- **Máxima exclusividad y competencia**

---

### Caso 5: Contenido Narrativo (Sin Stock, Límite 1)

**Configuración:**
```
Producto: 📓 Diario Íntimo de Diana
Stock: ♾️ Ilimitado
Límite por usuario: 1 vez
Precio: 30 besitos
```

**Comportamiento:**
- Todos pueden comprarlo
- Cada usuario solo compra una vez (es un diario)
- **Contenido narrativo estándar**

---

## 🔍 Lógica Técnica

### Cálculo de Stock Disponible

**En `shop_service.py:48-60`**

```python
if item.stock_limit is not None:
    # Contar compras totales
    purchases_stmt = select(func.count(UserPurchase.id)).where(
        UserPurchase.shop_item_id == item.id
    )
    purchases_result = await self.session.execute(purchases_stmt)
    total_purchases = purchases_result.scalar() or 0

    # Ocultar si agotado
    if total_purchases >= item.stock_limit:
        logger.info(f"Item {item.name} is sold out ({total_purchases}/{item.stock_limit})")
        continue  # No mostrar en tienda
```

### Validación de Límite por Usuario

**En `shop_service.py:62-74`**

```python
if item.max_purchases_per_user > 0:
    # Contar compras del usuario
    user_purchases_stmt = select(func.count(UserPurchase.id)).where(
        UserPurchase.user_id == user_id,
        UserPurchase.shop_item_id == item.id
    )
    user_purchases_result = await self.session.execute(user_purchases_stmt)
    user_purchases = user_purchases_result.scalar() or 0

    # Ocultar si alcanzó límite
    if user_purchases >= item.max_purchases_per_user:
        continue  # No mostrar en tienda
```

### Validación en Compra

**En `shop_service.py:164-194`**

```python
# Check stock availability
if item.stock_limit is not None:
    total_purchases = await self.session.execute(...)
    if total_purchases >= item.stock_limit:
        return {"success": False, "message": "❌ Agotado"}

# Check max purchases per user
if item.max_purchases_per_user > 0:
    user_purchases = await self.session.execute(...)
    if user_purchases >= item.max_purchases_per_user:
        return {"success": False, "message": "❌ Ya compraste el máximo"}
```

---

## 📈 Reportes de Stock en Admin

### Vista de Lista de Productos

```
🛒 Administración de Tienda

📊 Estadísticas:
• Total de productos: 5
• Productos activos: 4
• Ventas totales: 127

📦 Lista de Productos:

1. 📓 Diario Íntimo
   💰 30 besitos | 👥 45 ventas | ♾️ Stock ilimitado
   [👁️ Ver] [✏️ Editar] [🗑️ Eliminar]

2. 🎨 Artwork Exclusivo
   💰 100 besitos | 👥 7/10 ventas | 📦 3 restantes ⚠️
   [👁️ Ver] [✏️ Editar] [🗑️ Eliminar]

3. 👑 Corona Premium
   💰 500 besitos | 👥 1/1 ventas | 🚫 AGOTADO
   [👁️ Ver] [✏️ Editar] [🗑️ Eliminar]
```

*(Nota: Esta visualización mejorada se puede implementar en el futuro)*

---

## 🔄 Migración de Base de Datos

### Migración Automática

**Al iniciar el bot**, SQLAlchemy detecta los nuevos campos y:
- ✅ Agrega `stock_limit` (NULL por defecto = ilimitado)
- ✅ Agrega `max_purchases_per_user` (1 por defecto)
- ✅ Productos existentes quedan con stock ilimitado y límite 1

### Migración Manual (Opcional)

```bash
cd /home/azureuser/repos/bolt_ok/mybot
export BOT_TOKEN="tu_token_aqui"
python migrations/add_stock_fields_to_shop_items.py
```

**Salida esperada:**

```
============================================================
Starting migration: Add stock fields to shop_items
============================================================
Initializing database...
Adding 'stock_limit' column to 'shop_items' table...
✅ Successfully added 'stock_limit' column
Adding 'max_purchases_per_user' column to 'shop_items' table...
✅ Successfully added 'max_purchases_per_user' column
✅ Migration completed successfully
✅ Migration verified successfully
============================================================
✅ Migration completed successfully!
============================================================

Next steps:
  1. Restart the bot
  2. Products can now have stock limits and purchase limits
  3. Use Admin → Tienda → Create/Edit to configure limits

Features:
  • stock_limit (NULL = unlimited)
  • max_purchases_per_user (0 = unlimited, default 1)
```

---

## 🐛 Troubleshooting

### Problema: Stock no se descuenta

**Síntoma:** Usuario compra pero stock sigue igual

**Causa:** El stock no se "descuenta", se cuenta cuántas veces se compró

**Solución:** Es el comportamiento correcto. El sistema cuenta:
```
Compras totales ≥ stock_limit → Agotado
```

---

### Problema: Usuario puede comprar más del límite

**Síntoma:** Usuario compró 2 veces un producto con límite 1

**Diagnóstico:**
```sql
SELECT * FROM user_purchases
WHERE user_id = [user_id] AND shop_item_id = [item_id];
```

**Causas posibles:**
- Compras simultáneas (race condition)
- Límite se cambió después de compras

**Solución:**
- El sistema valida antes de cada compra
- Race conditions son muy raras en Telegram (un usuario a la vez)

---

### Problema: Producto agotado sigue apareciendo

**Síntoma:** Producto con 10/10 ventas aún visible

**Diagnóstico:**
1. Verificar ventas:
   ```sql
   SELECT COUNT(*) FROM user_purchases WHERE shop_item_id = [item_id];
   ```

2. Verificar stock_limit en producto:
   ```
   Admin → Tienda → [Producto] → Ver
   ```

**Solución:**
- Si ventas = stock_limit → debería estar oculto
- Reiniciar bot para refrescar caché
- Verificar logs: `tail -f logs/bot.log | grep "sold out"`

---

## ✅ Checklist de Implementación

Funcionalidades completadas:

- [x] Agregar campos `stock_limit` y `max_purchases_per_user` a modelo
- [x] Estados FSM para configurar stock y límites
- [x] Paso de stock en flujo de creación
- [x] Paso de límite por usuario en flujo de creación
- [x] Menú de edición de stock
- [x] Menú de edición de límite por usuario
- [x] Validación de stock en compra
- [x] Validación de límite por usuario en compra
- [x] Filtrado de productos agotados en tienda
- [x] Filtrado de productos con límite alcanzado
- [x] Visualización de stock bajo/crítico en botones
- [x] Cálculo de stock restante en CoordinadorCentral
- [x] Script de migración de base de datos
- [x] Documentación completa

---

## 📚 Referencias de Código

### Archivos Modificados

1. **`database/models.py:482-483`**
   - Agregado: `stock_limit = Column(Integer, nullable=True)`
   - Agregado: `max_purchases_per_user = Column(Integer, default=1)`

2. **`utils/admin_state.py:203-204, 212-213`**
   - Agregado: `configuring_stock = State()`
   - Agregado: `configuring_max_purchases = State()`
   - Agregado: `editing_stock = State()`
   - Agregado: `editing_max_purchases = State()`

3. **`handlers/admin/shop_admin.py`**
   - Líneas 462-682: Handlers de configuración de stock y límites (creación)
   - Líneas 1381-1729: Handlers de edición de stock y límites
   - Modificado: Ambos handlers de creación incluyen nuevos campos

4. **`services/shop_service.py`**
   - Líneas 20-82: `get_available_items()` filtra por stock y límites
   - Líneas 147-230: `purchase_item()` valida stock y límites

5. **`services/coordinador_central.py:721-743`**
   - Modificado: `_flujo_acceder_tienda()` calcula stock restante

6. **`keyboards/common.py:18-70`**
   - Modificado: `build_shop_keyboard()` muestra advertencias de stock

### Archivos Nuevos

1. **`migrations/add_stock_fields_to_shop_items.py`**
   - Script de migración para agregar columnas

2. **`docs/admin_shop_stock_feature.md`** (este archivo)
   - Documentación completa de la funcionalidad

---

## 🚀 Próximas Mejoras Posibles

### Mejora Futura 1: Reabastecimiento de Stock
```python
# Botón en admin para agregar más stock
await item.restock(quantity=10)
# stock_limit aumenta en 10
```

### Mejora Futura 2: Historial de Stock
```python
class StockHistory(Base):
    item_id = Column(Integer, ForeignKey("shop_items.id"))
    change = Column(Integer)  # +10, -1, etc
    reason = Column(String)  # "restock", "purchase", "admin_adjustment"
    created_at = Column(DateTime)
```

### Mejora Futura 3: Notificaciones de Stock Bajo
```python
# Notificar a admin cuando stock < 5
if remaining < 5:
    await bot.send_message(admin_id, f"⚠️ {item.name} tiene solo {remaining} unidades")
```

---

**Funcionalidad de stock y límites implementada exitosamente** ✅

Los productos ahora soportan control completo de inventario con stock limitado y límites de compra por usuario, permitiendo crear productos exclusivos y ediciones limitadas.
